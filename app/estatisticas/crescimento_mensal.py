from typing import List

from app.estatisticas.stats_utils import historico_balanca_dataframe, historico_vlfob_dataframe
from app.models.vidente import Vidente
from app.utils.logging_config import app_logger, error_logger
from app import cache


@cache.memoize(timeout=60*60*24)
def crescimento_mensal_vlfob(tipo:str, ncm:List[int]=None, estados:List[int]=None, paises:List[int]=None):
    try:
        df = historico_vlfob_dataframe(tipo, ncm, estados, paises)
        df['crescimento'] = df[f'valor_fob_{tipo}'].pct_change().fillna(0) * 100
        df_resultado = df[['DATA', 'crescimento']].rename(columns={'DATA': 'ds', 'crescimento': 'y'})
        vidente = Vidente()
        return vidente.gerar_profecia_json(df_resultado)
    except:
        return None


@cache.memoize(timeout=60*60*24)
def crescimento_mensal_balanca(ncm:List[int]=None, estados:List[int]=None, paises:List[int]=None):
    try:
        df = historico_balanca_dataframe(ncm, estados, paises)
        df['crescimento'] = df[f'balanca_comercial'].pct_change().fillna(0) * 100
        df_resultado = df[['DATA', 'crescimento']].rename(columns={'DATA': 'ds', 'crescimento': 'y'})
        vidente = Vidente()
        return vidente.gerar_profecia_json(df_resultado)
    except:
        return None