from app import cache
from typing import List, Literal
import pandas as pd
from psycopg2 import Error, OperationalError
from psycopg2.extras import DictCursor

from app.dao.dao_utils import build_where
from app.database.database_connection import get_connection
from app.estatisticas.stats_utils import historico_imp_exp_dataframe
from app.utils.logging_config import app_logger, error_logger


@cache.memoize(timeout=60*60*24)
def analise_sazonalidade(df: pd.DataFrame):
    """
    Realiza análise de sazonalidade dos dados de exportação e importação,
    desconsiderando registros com valores zerados, e retorna dados para gráficos.
    """

    df['DATA'] = pd.to_datetime(df['DATA'])
    df['mes'] = df['DATA'].dt.month 

    # Filtra valores maiores que zero
    df_export = df[df['valor_fob_exp'] > 0]
    df_import = df[df['valor_fob_imp'] > 0]

    # Agrupa separadamente para evitar perda de dados relevantes
    exp_por_mes = df_export.groupby('mes')['valor_fob_exp'].sum()
    imp_por_mes = df_import.groupby('mes')['valor_fob_imp'].sum()

    # Junta os dois em um único DataFrame
    sazonalidade = pd.DataFrame({
        'valor_fob_exp': exp_por_mes,
        'valor_fob_imp': imp_por_mes
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
            'exportacoes': round(row['valor_fob_exp']/10, 2),
            'importacoes': round(row['valor_fob_imp']/10, 2),
        })

    return dados_json


@cache.memoize(timeout=60*60*24)
def analise_hhi(ncm: List[int] = None, estados: List[int] = None, paises: List[int] = None, crit: Literal["estado", "pais", "ncm"] = "estado"):
    filtro_col = {
        "estado": "id_estado",
        "pais": "id_pais",
        "ncm": "id_produto"
    }.get(crit)

    where_clause = build_where(paises=paises, estados=estados, ncm=ncm)
    where_clause = where_clause.replace("produto.id_ncm", "id_produto")

    query = f"""
        WITH base AS (
            SELECT 
                ano,
                {filtro_col},
                'exp' AS tipo,
                SUM(valor_fob_total) AS valor_fob
            FROM mv_exportacao_estado_anual
            {where_clause}
            GROUP BY ano, {filtro_col}

            UNION ALL

            SELECT 
                ano,
                {filtro_col},
                'imp' AS tipo,
                SUM(valor_fob_total) AS valor_fob
            FROM mv_importacao_estado_anual
            {where_clause}
            GROUP BY ano, {filtro_col}
        ),

        total_por_ano AS (
            SELECT 
                ano,
                tipo,
                SUM(valor_fob) AS total_fob
            FROM base
            GROUP BY ano, tipo
        ),

        participacoes AS (
            SELECT 
                b.ano,
                b.tipo,
                b.{filtro_col},
                b.valor_fob,
                t.total_fob,
                POWER(b.valor_fob / NULLIF(t.total_fob, 0), 2) AS participacao_quadrada
            FROM base b
            JOIN total_por_ano t
            ON b.ano = t.ano AND b.tipo = t.tipo
        )

        SELECT 
            ano,
            tipo,
            SUM(participacao_quadrada) AS hhi
        FROM participacoes
        GROUP BY ano, tipo
        ORDER BY ano;

    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                app_logger.info("iniciando busca hhi no banco de dados")
                cur.execute(query)
                rows = cur.fetchall()
                rows = [dict(row) for row in rows]
    except (Error, OperationalError) as e:
        error_logger.error(f"Erro ao acessar hhi no banco de dados: {str(e)}")

    app_logger.info("iniciando conversão para dataframe")
    df = pd.DataFrame(rows)
    if df.empty:
        app_logger.info("dataframe hhi está vazio")
        return []
    print(df)
    # df['DATA'] = pd.to_datetime(df['ano'].astype(str) + '-' + df['mes'].astype(str).str.zfill(2))
    df['DATA'] = pd.to_datetime(df['ano'].astype(str))
    df_pivot = df.pivot_table(
        index='ano',
        columns='tipo',
        values='hhi',
        aggfunc='sum'  # ou 'mean', conforme sua necessidade
    ).fillna(0).reset_index()
    df_pivot = df_pivot.rename(columns={'exp': 'hhi_exportacao', 'imp': 'hhi_importacao'})

    return df_pivot.round(4).to_dict(orient='records')


# @cache.memoize(timeout=60*60*24)
def gerar_estatisticas_auxiliares(ncm:List[int]=None, estados:List[int]=None, paises:List[int]=None):
    """
    Gera todos os dados para o dashboard em um único JSON com todas as análises.
    """

    try:
        df = historico_imp_exp_dataframe(ncm, estados, paises)
        sazonalidade = analise_sazonalidade(df)
        
        hhi_pais = analise_hhi(ncm, estados, paises, crit='pais')
        hhi_estado = analise_hhi(ncm, estados, paises, crit='estado')
        hhi_ncm = analise_hhi(ncm, estados, paises, crit='ncm')
        
        return {
            'sazonalidade': sazonalidade,
            'concentracao_pais': hhi_pais,
            'concentracao_estado': hhi_estado,
            'concentracao_ncm': hhi_ncm
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': e
        }