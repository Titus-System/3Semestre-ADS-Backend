from app import cache
import pandas as pd
from psycopg2 import Error, OperationalError
from psycopg2.extras import DictCursor

from app.database.database_connection import get_connection
from data_pipeline.models.vidente import Vidente


def get_dataframe_ncm(tipo:str, ncm:int=None, estado:int=None, pais:int=None) -> pd.DataFrame:
    where_statement = ""
    condicionais = []
    if ncm or estado or pais:
        if ncm:
            condicionais.append(f"id_produto = {ncm}")
        if estado:
            condicionais.append(f"id_estado = {estado}")
        if pais:
            condicionais.append(f"id_pais = {pais}")
        where_statement = "WHERE " + " AND ".join(condicionais)
    
    query = f"""
        SELECT ano, mes,
            SUM(valor_fob) as valor_fob_{tipo},
            SUM(kg_liquido) as kg_liquido_{tipo}
        FROM {tipo}ortacao_estado
        {where_statement}
        GROUP BY ano, mes
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query)
                res = [dict(row) for row in cur.fetchall()]
        print(res)
        if len(res) < 1:
            return pd.DataFrame(columns=['DATA', f'valor_fob_{tipo}', f'kg_liquido_{tipo}', f'valor_agregado_{tipo}' ]).fillna(0)
        df = pd.DataFrame(res)
        df[f'valor_fob_{tipo}'] = df[f'valor_fob_{tipo}'].astype(float)
        df[f'kg_liquido_{tipo}'] = df[f'kg_liquido_{tipo}'].astype(float)
        df[f'valor_agregado_{tipo}'] = df[f'valor_fob_{tipo}'] / df[f'kg_liquido_{tipo}'].replace(0, pd.NA)
        df['DATA'] = pd.to_datetime(df['ano'].astype(str) + '-' + df['mes'].astype(str).str.zfill(2))
        df = df.drop(columns=['ano', 'mes'])
        df['DATA'] = pd.to_datetime(df['DATA'])
        print(df.columns)
        return df
    except (Error, OperationalError) as e:
        print(f"[ERRO]: erro em tendencias_stats/get_dataframe_ncm: {str(e)}")


def get_videncia(df:pd.DataFrame, coluna_valor:str):
    vidente = Vidente()
    df_prophet = df.groupby('DATA')[[coluna_valor]].sum().reset_index()
    df_prophet = df_prophet.rename(columns={'DATA': 'ds', coluna_valor: 'y'})
    df_prophet['y'] = df_prophet['y'].fillna(0)
    return vidente.gerar_profecia_json(df_prophet)

@cache.memoize(timeout=60*60*24)
def tendencias_dashboard(ncm: int  = None, estado: str = None, pais: int = None):
    colunas_padrao = [
        'DATA',
        'valor_fob_exp',
        'kg_liquido_exp',
        'valor_agregado_exp',
        'valor_fob_imp',
        'kg_liquido_imp',
        'valor_agregado_imp'
    ]

    df_exp = get_dataframe_ncm('exp', ncm, estado, pais)
    df_imp = get_dataframe_ncm('imp', ncm, estado, pais)

    if df_exp is None or df_exp.empty:
        df_exp = pd.DataFrame(columns=colunas_padrao)
    if df_imp is None or df_imp.empty:
        df_imp = pd.DataFrame(columns=colunas_padrao)
            
    df = pd.concat([df_exp, df_imp], ignore_index=True)
    df = df.groupby('DATA').sum(numeric_only=True).reset_index()
    print("df_concat: ", df)

    for col in colunas_padrao:
        df[col] = df.get(col, 0)
    
    df['balanca'] = df['valor_fob_exp'].fillna(0) - df['valor_fob_imp'].fillna(0)

    tendencia_dashboard = {
        'vl_fob_exp': get_videncia(df, 'valor_fob_exp'),
        'vl_fob_imp': get_videncia(df, 'valor_fob_imp'),
        'kg_liquido_exp': get_videncia(df, 'kg_liquido_exp'), 
        'kg_liquido_imp': get_videncia(df, 'kg_liquido_imp'),
        'valor_agregado_exp': get_videncia(df, 'valor_agregado_exp'),
        'valor_agregado_imp': get_videncia(df, 'valor_agregado_imp'),
        'balanca': get_videncia(df, 'balanca') 
    }
    return tendencia_dashboard