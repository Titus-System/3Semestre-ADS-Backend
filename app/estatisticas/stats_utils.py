from typing import List
import pandas as pd
from psycopg2 import Error, OperationalError
from psycopg2.extras import DictCursor

from app.dao.dao_utils import build_where
from app.database.database_connection import get_connection
from app.utils.logging_config import app_logger, error_logger



def filtrar_df(
    df: pd.DataFrame,
    ncm: int = None,
    estado: str = None,
    pais: int = None,
    via: int = None,
    urf: int = None,
    sh4: str = None,
) -> pd.DataFrame:
    """
    Filtra um DataFrame de comércio exterior com base em múltiplos critérios opcionais.
    """
    if ncm is not None:
        df = df[df['CO_NCM'] == ncm]
    if estado is not None:
        df = df[df['SG_UF_NCM'] == estado]
    if pais is not None:
        df = df[df['CO_PAIS'] == pais]
    if via is not None:
        df = df[df['CO_VIA'] == via]
    if urf is not None:
        df = df[df['CO_URF'] == urf]
    if sh4 is not None:
        df = df[df['CO_SH4'] == sh4]
    return df


def historico_vlfob_dataframe(tipo:str, ncm:List[int]=None, estados:List[int]=None, paises:List[int]=None) -> pd.DataFrame:
    where_statement = build_where(paises=paises, estados=estados, ncm=ncm)
    where_statement = where_statement.replace("produto.id_ncm", "id_produto")
    query = f"""
        SELECT ano, mes,
            SUM(valor_fob) as valor_fob
        FROM {tipo}ortacao_estado
        {where_statement}
        GROUP BY ano, mes
    """
    print(query)
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query)
                res = cur.fetchall()
                app_logger.info("busca de hostórico de vlfob buscado para calculo de regressão linear")
                hist = [dict(row) for row in res]
    except (Error, OperationalError):
        error_logger.error("Erro ao buscar histórico de vlfob para cálculo da regressão linear")
        return
    
    dict_filtrado = []
    for row in hist:
        dict_filtrado.append(
            {
                'ano': row.get('ano'),
                'mes': row.get('mes'),
                f'valor_fob_{tipo}':row.get('valor_fob')
            }
        )
    if not dict_filtrado: return pd.DataFrame(columns=['DATA', f'valor_fob_{tipo}'])
    df = pd.DataFrame(dict_filtrado)
    df[f'valor_fob_{tipo}'] = df[f'valor_fob_{tipo}'].astype(float)
    df['DATA'] = pd.to_datetime(df['ano'].astype(str) + '-' + df['mes'].astype(str).str.zfill(2))
    df = df.drop(columns=['ano', 'mes'])
    df = df.fillna(0)
    return df if len(df) > 0 else pd.DataFrame(columns=['DATA', f'valor_fob_{tipo}'])


def historico_imp_exp_dataframe(ncm:List[int]=None, estados:List[int]=None, paises:List[int]=None):
    hist_exp = historico_vlfob_dataframe("exp", ncm, estados, paises)
    hist_imp = historico_vlfob_dataframe("imp", ncm, estados, paises)
    hist = hist_exp.merge(hist_imp, how="outer", on="DATA")
    hist = hist.fillna(0)
    hist = hist.sort_values('DATA')
    return hist
    

def historico_balanca_dataframe(ncm:List[int]=None, estados:List[int]=None, paises:List[int]=None) -> pd.DataFrame:
    hist_exp = historico_vlfob_dataframe("exp", ncm, estados, paises)
    hist_imp = historico_vlfob_dataframe("imp", ncm, estados, paises)
    hist_balanca = hist_exp.merge(hist_imp, how="outer", on="DATA")
    hist_balanca = hist_balanca.fillna(0)
    hist_balanca['balanca_comercial'] = hist_balanca['valor_fob_exp'] - hist_balanca['valor_fob_imp']
    hist_balanca = hist_balanca.sort_values('DATA')
    return hist_balanca
