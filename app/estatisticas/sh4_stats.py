from app import cache
from typing import List, Literal
import pandas as pd

from app.dao import sh4_dao
from app.estatisticas.stats_utils import filtrar_df
from app.models.vidente import Vidente

path = 'data_pipeline/datasets/dados_agregados/mv_sh4_mensal.csv'

# 'CO_SH4,CO_PAIS,SG_UF_NCM,VL_FOB_EXP,KG_LIQUIDO_EXP,VL_FOB_IMP,KG_LIQUIDO_IMP,DATA'

def hist_sh4 (df:pd.DataFrame, tipo:str, crit=Literal['KG_LIQUIDO', 'VL_FOB', 'balanca', 'valor_agregado']):
    coluna_crit = f"{crit}_{tipo}" if crit != 'balanca' else crit
    df = df.groupby('DATA')[[coluna_crit]].sum().reset_index()
    df_prophet = df.rename(columns={'DATA': 'ds', coluna_crit: 'y'})
    df_prophet['y'] = df_prophet['y'].fillna(0)
    df_prophet['y'] = pd.to_numeric(df_prophet['y'], errors='coerce') 
    return df_prophet


@cache.memoize(timeout=60*60*24)
def tendencia_sh4(sh4: List[str], estado: List[int] = None, pais: List[int] = None):
    tendencia_dashboard = {}
    vidente = Vidente()  # Supondo que essa classe implemente .gerar_profecia_json()

    estado = (estado,) if estado else None
    pais = (pais,) if pais else None
    print("Argumentos recebidos:")
    print("sh4:", sh4)
    print("estado:", estado)
    print("pais:", pais)

    df_exp = pd.DataFrame(sh4_dao.sh4_hist('exp', sh4, pais, estado))
    df_exp.rename(columns={
        'total_valor_fob': 'VL_FOB_EXP',
        'total_kg_liquido': 'KG_LIQUIDO_EXP',
        'total_valor_agregado': 'valor_agregado_EXP'
    }, inplace=True)

    df_imp = pd.DataFrame(sh4_dao.sh4_hist('imp', sh4, pais, estado))
    df_imp.rename(columns={
        'total_valor_fob': 'VL_FOB_IMP',
        'total_kg_liquido': 'KG_LIQUIDO_IMP',
        'total_valor_agregado': 'valor_agregado_IMP'
    }, inplace=True)

    colunas_comuns = ['ano', 'mes', 'id_sh4', 'descricao']
    colunas_exp = colunas_comuns + ['VL_FOB_EXP', 'KG_LIQUIDO_EXP', 'valor_agregado_EXP']
    colunas_imp = colunas_comuns + ['VL_FOB_IMP', 'KG_LIQUIDO_IMP', 'valor_agregado_IMP']
    # Se estiver vazio, criar DataFrame com colunas esperadas
    if df_exp.empty:
        df_exp = pd.DataFrame(columns=colunas_exp)

    if df_imp.empty:
        df_imp = pd.DataFrame(columns=colunas_imp)

    
    print(df_exp)
    print(df_imp)

    df = pd.merge(df_exp, df_imp, on=['ano', 'mes', 'id_sh4', 'descricao'], how='outer')
    df['ano'] = df['ano'].astype(int)
    df['mes'] = df['mes'].astype(int)

    df['DATA'] = pd.to_datetime(df['ano'].astype(str) + '-' + df['mes'].astype(str).str.zfill(2))
    df = df.fillna(0)
    df = df.groupby('DATA').agg({
        'VL_FOB_EXP': 'sum',
        'VL_FOB_IMP': 'sum',
        'KG_LIQUIDO_EXP': 'sum',
        'KG_LIQUIDO_IMP': 'sum',
        'valor_agregado_EXP': 'mean',
        'valor_agregado_IMP': 'mean'
    }).reset_index()

    df['balanca'] = df['VL_FOB_EXP'] - df['VL_FOB_IMP']
    df['valor_agregado_EXP'] = df['VL_FOB_EXP'] / df['KG_LIQUIDO_EXP'].replace(0, pd.NA)
    df['valor_agregado_IMP'] = df['VL_FOB_IMP'] / df['KG_LIQUIDO_IMP'].replace(0, pd.NA)
    print("df após a filtragem: ", df)
    # Geração de tendências
    for crit in ['KG_LIQUIDO', 'VL_FOB', 'balanca', 'valor_agregado']:
        if crit != 'balanca':
            for tipo in ['EXP', 'IMP']:
                nome = f"{crit.lower()}_{tipo.lower()}"
                try:
                    df_temp = hist_sh4(df, tipo, crit)
                    tendencia = vidente.gerar_profecia_json(df_temp)
                    tendencia_dashboard[nome] = tendencia
                except Exception as e:
                    print(f"[ERRO] Falha ao gerar tendência para {nome}: {e}")
        else:
            nome = crit.lower()
            try:
                df_temp = hist_sh4(df, None, crit)
                tendencia = vidente.gerar_profecia_json(df_temp)
                tendencia_dashboard[nome] = tendencia
            except Exception as e:
                print(f"[ERRO] Falha ao gerar tendência para {nome}: {e}")
    print(tendencia_dashboard.keys())

    return tendencia_dashboard
