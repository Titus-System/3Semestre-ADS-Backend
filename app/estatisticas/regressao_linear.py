from typing import List, Literal
import pandas as pd
from sklearn.linear_model import LinearRegression

from app.estatisticas.stats_utils import historico_balanca_dataframe, historico_vlfob_dataframe
from app.utils.logging_config import app_logger, error_logger
from app import cache


@cache.memoize(timeout=60*60*24)
def calcular_regressao_linear (crit:Literal["valor_fob", "balanca"], tipo:str=None, ncm:List[int]=None, estados:List[int]=None, paises:List[int]=None):
    if crit == 'valor_fob':
        df = historico_vlfob_dataframe(tipo, ncm, estados, paises)
        df['timestamp'] = df['DATA'].map(pd.Timestamp.timestamp)
        X = df[['timestamp']]
        y = df[f'valor_fob_{tipo}']
    else:
        df = historico_balanca_dataframe(ncm, estados, paises)
        df['timestamp'] = df['DATA'].map(pd.Timestamp.timestamp)
        X = df[['timestamp']]
        y = df['balanca_comercial']
    
    try:
        modelo = LinearRegression()
        modelo.fit(X, y)
        previsoes = modelo.predict(X)
        df_resultado = pd.DataFrame({
            'ds': df['DATA'].astype(str),
            'y_real': y,
            'y_regressao': previsoes
        })
        return {
            "dados": df_resultado.to_dict(orient='records'),
            "coeficiente_angular": modelo.coef_[0],
            "intercepto": modelo.intercept_,
            "r2": modelo.score(X, y)
        }
    except Exception as e:
        error_logger.error(f"Erro ao gerar Regrassão linear: {e}")
        return {
            "dados": {},
            "coeficiente_angular": 0,
            "intercepto": 0,
            "r2": 0
        } 



def regressao_linear_vlfob(tipo:str, ncm:List[int]=None, estados:List[int]=None, paises:List[int]=None) -> dict:
    df = historico_vlfob_dataframe(tipo, ncm, estados, paises)
    if df is None : return None
    tipo = tipo.upper()
    df['timestamp'] = df['DATA'].map(pd.Timestamp.timestamp)
    X = df[['timestamp']]
    y = df[f'VL_FOB_{tipo}']
    modelo = LinearRegression()
    modelo.fit(X, y)
    previsoes = modelo.predict(X)
    df_resultado = pd.DataFrame({
        'ds': df['DATA'].astype(str),
        'y_real': y,
        'y_regressao': previsoes
    })
    return {
        "dados": df_resultado.to_dict(orient='records'),
        "coeficiente_angular": modelo.coef_[0],
        "intercepto": modelo.intercept_,
        "r2": modelo.score(X, y)
    }


def regressao_linear_balanca_comercial(ncm:List[int]=None, estados:List[int]=None, paises:List[int]=None) -> dict:
    df = historico_balanca_dataframe(ncm, estados, paises)
    df = df.groupby('DATA')[[f'balanca_comercial']].sum().reset_index()
    df['DATA'] = pd.to_datetime(df['DATA'])
    df = df.sort_values('DATA')
    df['timestamp'] = df['DATA'].map(pd.Timestamp.timestamp)
    X = df[['timestamp']]
    y = df[f'balanca_comercial']
    modelo = LinearRegression()
    modelo.fit(X, y)
    previsoes = modelo.predict(X)
    df_resultado = pd.DataFrame({
        'ds': df['DATA'].astype(str),
        'y_real': y,
        'y_regressao': previsoes
    })
    return {
        "dados": df_resultado.to_dict(orient='records'),
        "coeficiente_angular": modelo.coef_[0],
        "intercepto": modelo.intercept_,
        "r2": modelo.score(X, y)
    }
