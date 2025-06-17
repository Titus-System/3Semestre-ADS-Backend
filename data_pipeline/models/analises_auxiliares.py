from app import cache
from typing import Literal
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
from datetime import datetime, timedelta


def analise_sazonalidade(df: pd.DataFrame, ncm:int|None = None, estado:str|None=None, pais:str|None=None):
    """
    Realiza análise de sazonalidade dos dados de exportação e importação,
    desconsiderando registros com valores zerados, e retorna dados para gráficos.
    """
    if ncm:
        df = df[df['CO_NCM'] == ncm]
    if estado:
        df = df[df['SG_UF_NCM'] == estado]
    if pais:
        df = df[df['CO_PAIS'] == pais]
    df = df.fillna(0)
    df['DATA'] = pd.to_datetime(df['DATA'])
    df['mes'] = df['DATA'].dt.month 

    # Filtra valores maiores que zero
    df_export = df[df['VL_FOB_EXP'] > 0]
    df_import = df[df['VL_FOB_IMP'] > 0]

    # Agrupa separadamente para evitar perda de dados relevantes
    exp_por_mes = df_export.groupby('mes')['VL_FOB_EXP'].sum()
    imp_por_mes = df_import.groupby('mes')['VL_FOB_IMP'].sum()

    # Junta os dois em um único DataFrame
    sazonalidade = pd.DataFrame({
        'VL_FOB_EXP': exp_por_mes,
        'VL_FOB_IMP': imp_por_mes
    }).fillna(0).reset_index()

    # Nome dos meses
    nome_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    sazonalidade['mes_nome'] = sazonalidade['mes'].apply(lambda x: nome_meses[x-1])

    # Monta JSON para gráfico
    dados_json = []
    for _, row in sazonalidade.iterrows():
        dados_json.append({
            'mes': row['mes_nome'],
            'exportacoes': round(row['VL_FOB_EXP']/10, 2),
            'importacoes': round(row['VL_FOB_IMP']/10, 2),
        })

    return dados_json



def analise_hhi(
    crit: Literal["estado", "pais", "ncm"],
    df: pd.DataFrame,
    ncm: int | None = None,
    estado: str | None = None,
    pais: int | None = None
):
    """
    Calcula o Índice Herfindahl-Hirschman (HHI) por mês, para exportações e importações,
    com base na concentração por país ou estado.
    """

    if ncm:
        df = df[df['CO_NCM'] == ncm]
    if estado:
        df = df[df['SG_UF_NCM'] == estado]
    if pais:
        df = df[df['CO_PAIS'] == pais]
    
    df=df.fillna(0)

    if crit not in ["estado", "pais", "ncm"]:
        raise ValueError("O critério deve ser 'estado' ou 'pais'.")

    if crit == 'estado':
        filtro = "SG_UF_NCM"
    elif crit == 'pais':
        filtro = "CO_PAIS"
    else:
        filtro = "CO_NCM"

    df['DATA'] = pd.to_datetime(df['DATA'])

    df_grouped = df.groupby([pd.Grouper(key='DATA', freq='MS'), filtro]).agg({
        'VL_FOB_EXP': 'sum',
        'VL_FOB_IMP': 'sum'
    }).reset_index()

    df_long = df_grouped.melt(
        id_vars=['DATA', filtro],
        value_vars=['VL_FOB_EXP', 'VL_FOB_IMP'],
        var_name='tipo',
        value_name='valor'
    )

    df_long['tipo'] = df_long['tipo'].map({
        'VL_FOB_EXP': 'exportacao',
        'VL_FOB_IMP': 'importacao'
    })

    df_long['total_mes'] = df_long.groupby(['DATA', 'tipo'])['valor'].transform('sum')
    df_long['participacao'] = df_long['valor'] / df_long['total_mes']

    df_hhi = df_long.groupby(['DATA', 'tipo'])['participacao'] \
        .apply(lambda x: (x**2).sum()).reset_index(name='hhi')

    df_hhi_pivot = df_hhi.pivot(index='DATA', columns='tipo', values='hhi').reset_index()
    df_hhi_pivot['mes'] = df_hhi_pivot['DATA'].dt.strftime('%Y-%m')

    df_hhi_pivot = df_hhi_pivot.fillna(0).sort_values('DATA')

    dados_json = df_hhi_pivot[['mes', 'exportacao', 'importacao']].rename(
        columns={'exportacao': 'hhi_exportacao', 'importacao': 'hhi_importacao'}
    ).round(4).to_dict(orient='records')

    return dados_json


@cache.memoize(timeout=60*60*24)
def gerar_estatisticas_auxiliares_vlfob(ncm:int|None = None, estado:str|None=None, pais:str|None=None):
    """
    Gera todos os dados para o dashboard em um único JSON com todas as análises.
    """
    if ncm:
        df = pd.read_csv('data_pipeline/datasets/dados_agregados/mv_ncm_mensal.csv')
    else:
        df = pd.read_csv("data_pipeline/datasets/dados_agregados/mv_balanca_comercial.csv")

    try:
        sazonalidade = analise_sazonalidade(df, ncm, estado, pais)
        hhi_pais = analise_hhi(df=df, pais=pais, estado=estado, ncm=ncm, crit='pais')
        hhi_estado = analise_hhi(df=df, pais=pais, estado=estado, ncm=ncm, crit='estado')
        if ncm:
            hhi_ncm = analise_hhi(df=df, pais=pais, estado=estado, ncm=ncm, crit='ncm')
        else:
            df = pd.read_csv('data_pipeline/datasets/dados_agregados/mv_ncm_mensal.csv')
            hhi_ncm = analise_hhi(df=df, pais=pais, estado=estado, ncm=ncm, crit='ncm')
        return {
            'sazonalidade': sazonalidade,
            'concentracao_pais': hhi_pais,
            'concentracao_estado': hhi_estado,
            'concentracao_ncm': hhi_ncm
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }