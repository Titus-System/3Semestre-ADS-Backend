from typing import List

from app.estatisticas.stats_utils import historico_balanca_dataframe, historico_vlfob_dataframe
from app.models.vidente import Vidente
# from app.utils.logging_config import app_logger, error_logger
from app import cache


@cache.memoize(timeout=60*60*24)
def volatilidade_vlfob(tipo:str, ncm:List[int]=None, estados:List[int]=None, paises:List[int]=None):
    df = historico_vlfob_dataframe(tipo, ncm, estados, paises)
    if df is None : return None
    df['volatilidade'] = df[f'valor_fob_{tipo}'].rolling(window=6).std().fillna(0)
    df_resultado = df[['DATA', 'volatilidade']].rename(columns={'DATA': 'ds', 'volatilidade': 'y'})
    vidente = Vidente()
    return vidente.gerar_profecia_json(df_resultado)


@cache.memoize(timeout=60*60*24)
def volatilidade_balanca(ncm:List[int]=None, estados:List[int]=None, paises:List[int]=None):
    df = historico_balanca_dataframe(ncm, estados, paises)
    df['volatilidade'] = df[f'balanca_comercial'].rolling(window=6).std().fillna(0)
    df_resultado = df[['DATA', 'volatilidade']].rename(columns={'DATA': 'ds', 'volatilidade': 'y'})
    vidente = Vidente()
    return vidente.gerar_profecia_json(df_resultado)