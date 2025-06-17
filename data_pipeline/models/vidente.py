from app import cache
import json
import os
from typing import List, Literal
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.statespace.sarimax import SARIMAX
import statsmodels.api as smapi
from pandas.tseries.offsets import MonthEnd
import warnings

from data_pipeline.models.gera_dataframes import GeradorDeDataFrames
from app.utils.logging_config import app_logger, error_logger


warnings.filterwarnings("ignore")


class Vidente():
    def __init__(self):
        self.gd = GeradorDeDataFrames()
        self.output_dir = 'data_pipeline/datasets/tendencias'
        os.makedirs(self.output_dir, exist_ok=True)
        return
    

    def gerar_profecia(self, df_prophet: pd.DataFrame, nome_arquivo: str, titulo_graf: str, ylabel: str):
        if len(df_prophet) < 2:
            print("Dados insuficientes para modelagem.")
            return

        df = df_prophet.copy()
        df['ds'] = pd.to_datetime(df['ds'])
        df.set_index('ds', inplace=True)
        df = df.asfreq('MS')  #frequência mensal com início no início do mês
        df['y'] = df['y'].interpolate() 

        modelo = SARIMAX(df['y'], order=(1,1,1), seasonal_order=(1,1,1,12), enforce_stationarity=False, enforce_invertibility=False)
        modelo_fit = modelo.fit(disp=False)

        n_periods = 24
        future_index = pd.date_range(start=df.index[-1] + MonthEnd(1), periods=n_periods, freq='MS')
        previsoes = modelo_fit.forecast(steps=n_periods)

        df_previsao = pd.concat([df['y'], pd.Series(previsoes, index=future_index)], axis=0)
        
        # plt.figure(figsize=(10, 5))
        # df_previsao.plot(label='Previsão')
        # plt.axvline(df.index[-1], color='gray', linestyle='--', label='Início da previsão')
        # plt.title(titulo_graf)
        # plt.xlabel('Data')
        # plt.ylabel(ylabel)
        # plt.legend()
        # plt.grid(True)
        # plt.tight_layout()
        # plt.savefig(f'{self.output_dir}/{nome_arquivo}.png', dpi=300)
        # plt.close()

        resultado = df_previsao.reset_index()
        resultado.columns = ['ds', 'yhat']
        resultado['ds'] = resultado['ds'].astype(str)

        app_logger.info(f"Análise de tendências {nome_arquivo} finalizada")
        return resultado.to_dict(orient='records')
    

    def gerar_profecia_json(self, df_prophet):
        if len(df_prophet) < 2:
            print("Dados insuficientes para modelagem.")
            return

        df = df_prophet.copy()
        df['ds'] = pd.to_datetime(df['ds'])
        df.set_index('ds', inplace=True)
        df = df.asfreq('MS')  #frequência mensal com início no início do mês
        df['y'] = df['y'].interpolate() 

        modelo = SARIMAX(df['y'], order=(1,1,1), seasonal_order=(1,1,0,12), enforce_stationarity=False, enforce_invertibility=False)
        modelo_fit = modelo.fit(disp=False)

        n_periods = 24
        future_index = pd.date_range(start=df.index[-1] + MonthEnd(1), periods=n_periods, freq='MS')
        previsoes = modelo_fit.forecast(steps=n_periods)

        df_previsao = pd.concat([df['y'], pd.Series(previsoes, index=future_index)], axis=0)

        resultado = df_previsao.reset_index()
        resultado.columns = ['ds', 'yhat']
        resultado['ds'] = resultado['ds'].astype(str)

        app_logger.info(f"Análise de tendências finalizada")
        return resultado.to_dict(orient='records')


    @cache.memoize(timeout=60*60*24)
    def tendencia_balanca_comercial(self, 
        estado: str|None = None,
        pais: int|None = None
    ) -> List[dict] | None:
        app_logger.info(f"Iniciando análise de tendência de Balança Comercial")        
        df = pd.read_csv("data_pipeline/datasets/dados_agregados/mv_balanca_comercial.csv")

        if estado:
            df = df[df['SG_UF_NCM'] == estado]
        if pais:
            df = df[df['CO_PAIS'] == pais]

        df = df.groupby('DATA')[['balanca_comercial']].sum().reset_index()
        df_prophet = df[['DATA', 'balanca_comercial']].rename(columns={'DATA': 'ds', 'balanca_comercial': 'y'})
        df_prophet['y'] = df_prophet['y'].fillna(0)

        nome = f"tendencia_balanca_comercial"
        if estado:
            nome += f"_e{estado}"
        if pais:
            nome += f"_p{pais}"
        return self.gerar_profecia(df_prophet, nome, f"Previsão de Balança Comercial", "Balança Comercial ($)")

    @cache.memoize(timeout=60*60*24)
    def regressao_linear_balanca_comercial(self, estado: str | None = None, pais: int | None = None) -> dict:
        df = pd.read_csv("data_pipeline/datasets/dados_agregados/mv_balanca_comercial.csv")
        if estado:
            df = df[df['SG_UF_NCM'] == estado]
        if pais:
            df = df[df['CO_PAIS'] == pais]
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
    

    @cache.memoize(timeout=60*60*24)
    def crescimento_mensal_balanca_comercial(self, estado: str | None = None, pais: int | None = None) -> List[dict]:
        df = pd.read_csv("data_pipeline/datasets/dados_agregados/mv_balanca_comercial.csv")
        if estado:
            df = df[df['SG_UF_NCM'] == estado]
        if pais:
            df = df[df['CO_PAIS'] == pais]
        df = df.groupby('DATA')[[f'balanca_comercial']].sum().reset_index()
        df['DATA'] = pd.to_datetime(df['DATA'])
        df = df.sort_values('DATA')
        df['crescimento'] = df[f'balanca_comercial'].pct_change().fillna(0) * 100
        df_resultado = df[['DATA', 'crescimento']].rename(columns={'DATA': 'ds', 'crescimento': 'y'})
        # df_resultado['ds'] = df_resultado['ds'].astype(str)
        # return df_resultado.to_dict(orient='records')
        nome = f"tendencia_crescimento_mensal_balanca"
        if estado:
            nome += f"_e{estado}"
        if pais:
            nome += f"_p{pais}"
        return self.gerar_profecia(df_resultado, nome, "Crescimento Mensal da balança comercial", f"Taxa de crescimento")


    @cache.memoize(timeout=60*60*24)
    def volatilidade_balanca_comercial(self, estado: str | None = None, pais: int | None = None) -> List[dict]:
        df = pd.read_csv("data_pipeline/datasets/dados_agregados/mv_balanca_comercial.csv")
        if estado:
            df = df[df['SG_UF_NCM'] == estado]
        if pais:
            df = df[df['CO_PAIS'] == pais]
        df = df.groupby('DATA')[[f'balanca_comercial']].sum().reset_index()
        df['DATA'] = pd.to_datetime(df['DATA'])
        df = df.sort_values('DATA')
        df['volatilidade'] = df[f'balanca_comercial'].rolling(window=6).std().fillna(0)
        df_resultado = df[['DATA', 'volatilidade']].rename(columns={'DATA': 'ds', 'volatilidade': 'y'})
        # df_resultado['ds'] = df_resultado['ds'].astype(str)
        # return df_resultado.to_dict(orient='records')
        nome = f"tendencia_volatilidade_balanca"
        if estado:
            nome += f"_e{estado}"
        if pais:
            nome += f"_p{pais}"
        return self.gerar_profecia(df_resultado, nome, "Volatilidade da Balança Comercial", f"Volatiliade")



    @cache.memoize(timeout=60*60*24)
    def tendencia_vlfob(self, 
        tipo: Literal['EXP', 'IMP'],
        estado: str|None = None,
        pais: int|None = None
    ) -> List[dict]:
        app_logger.info(f"Iniciando análise de tendência de Valor FOB de {tipo}")
        df = pd.read_csv("data_pipeline/datasets/dados_agregados/mv_balanca_comercial.csv")

        if estado:
            df = df[df['SG_UF_NCM'] == estado]
        if pais:
            df = df[df['CO_PAIS'] == pais]

        df = df.groupby('DATA')[[f'VL_FOB_{tipo}']].sum().reset_index()
        df_prophet = df[['DATA', f'VL_FOB_{tipo}']].rename(columns={'DATA': 'ds', f'VL_FOB_{tipo}': 'y'})
        df_prophet['y'] = df_prophet['y'].fillna(0)

        nome = f"tendencia_vlfob_{tipo.lower()}"
        if estado:
            nome += f"_e{estado}"
        if pais:
            nome += f"_p{pais}"
        return self.gerar_profecia(df_prophet, nome, f"Previsão de Valor Fob de {tipo}", f"Valor Fob {tipo} ($)")
    

    @cache.memoize(timeout=60*60*24)
    def crescimento_mensal_vlfob(self, tipo: Literal['EXP', 'IMP'], estado: str | None = None, pais: int | None = None) -> List[dict]:
        df = pd.read_csv("data_pipeline/datasets/dados_agregados/mv_balanca_comercial.csv")
        if estado:
            df = df[df['SG_UF_NCM'] == estado]
        if pais:
            df = df[df['CO_PAIS'] == pais]
        df = df.groupby('DATA')[[f'VL_FOB_{tipo}']].sum().reset_index()
        df['DATA'] = pd.to_datetime(df['DATA'])
        df = df.sort_values('DATA')
        df['crescimento'] = df[f'VL_FOB_{tipo}'].pct_change().fillna(0) * 100
        df_resultado = df[['DATA', 'crescimento']].rename(columns={'DATA': 'ds', 'crescimento': 'y'})
        # df_resultado['ds'] = df_resultado['ds'].astype(str)
        # return df_resultado.to_dict(orient='records')
        nome = f"tendencia_crescimento_mensal_vlfob_{tipo.lower()}"
        if estado:
            nome += f"_e{estado}"
        if pais:
            nome += f"_p{pais}"
        return self.gerar_profecia(df_resultado, nome, "Crescimento Mensal do Valor Fob", f"Taxa de crescimento {tipo}")


    @cache.memoize(timeout=60*60*24)
    def volatilidade_vlfob(self, tipo: Literal['EXP', 'IMP'], estado: str | None = None, pais: int | None = None) -> List[dict]:
        df = pd.read_csv("data_pipeline/datasets/dados_agregados/mv_balanca_comercial.csv")
        if estado:
            df = df[df['SG_UF_NCM'] == estado]
        if pais:
            df = df[df['CO_PAIS'] == pais]
        df = df.groupby('DATA')[[f'VL_FOB_{tipo}']].sum().reset_index()
        df['DATA'] = pd.to_datetime(df['DATA'])
        df = df.sort_values('DATA')
        df['volatilidade'] = df[f'VL_FOB_{tipo}'].rolling(window=6).std().fillna(0)
        df_resultado = df[['DATA', 'volatilidade']].rename(columns={'DATA': 'ds', 'volatilidade': 'y'})
        # df_resultado['ds'] = df_resultado['ds'].astype(str)
        # return df_resultado.to_dict(orient='records')
        nome = f"tendencia_volatilidade_vlfob_{tipo.lower()}"
        if estado:
            nome += f"_e{estado}"
        if pais:
            nome += f"_p{pais}"
        return self.gerar_profecia(df_resultado, nome, "Volatilidade de Valor FOB", f"Volatiliade {tipo}")


    @cache.memoize(timeout=60*60*24)
    def regressao_linear_vlfob(self, tipo: Literal['EXP', 'IMP'], estado: str | None = None, pais: int | None = None) -> dict:
        df = pd.read_csv("data_pipeline/datasets/dados_agregados/mv_balanca_comercial.csv")
        if estado:
            df = df[df['SG_UF_NCM'] == estado]
        if pais:
            df = df[df['CO_PAIS'] == pais]
        df = df.groupby('DATA')[[f'VL_FOB_{tipo}']].sum().reset_index()
        df['DATA'] = pd.to_datetime(df['DATA'])
        df = df.sort_values('DATA')
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


    @cache.memoize(timeout=60*60*24)
    def tendencia_valor_agregado(self, tipo:Literal['EXP', 'IMP'], estado:str|None = None, pais:int|None = None) -> List[dict]:
        app_logger.info(f"Iniciando análise de tendência de Valor Agregado de {tipo}")
        df = pd.read_csv("data_pipeline/datasets/dados_agregados/mv_balanca_comercial.csv")
        if tipo == 'EXP':
            df = df.drop(columns=['VL_FOB_IMP', 'KG_LIQUIDO_IMP'])
        elif tipo == 'IMP':
            df = df.drop(columns=['VL_FOB_EXP', 'KG_LIQUIDO_EXP'])

        if estado:
            df = df[df['SG_UF_NCM'] == estado]
        if pais:
            df = df[df['CO_PAIS'] == pais]

        df = df.groupby('DATA')[[f'VL_FOB_{tipo}', f'KG_LIQUIDO_{tipo}']].sum().reset_index()
        df['valor_agregado'] = df[f'VL_FOB_{tipo}'] / df[f'KG_LIQUIDO_{tipo}']
        df_prophet = df[['DATA', 'valor_agregado']].rename(columns={'DATA': 'ds', 'valor_agregado': 'y'})
        df_prophet['y'] = df_prophet['y'].fillna(0)

        nome = f"tendencia_valor_agregado_{tipo.lower()}"
        if estado:
            nome += f"_e{estado}"
        if pais:
            nome += f"_p{pais}"
        return self.gerar_profecia(df_prophet, nome, f"Previsão de Valor Agregado médio de {tipo}", f"Valor Agregado médio {tipo} ($)")


    @cache.memoize(timeout=60*60*24)
    def tendencia_vlfob_ncm(self, tipo: Literal['EXP', 'IMP'], ncm: str) -> List[dict]:
        app_logger.info(f"Iniciando análise de tendência de VL_FOB por NCM {ncm} usando novo CSV")
        
        caminho_csv = (
            "data_pipeline/datasets/dados_agregados/mv_ncm_mensal_exp.csv"
            if tipo == "EXP" else
            "data_pipeline/datasets/dados_agregados/mv_ncm_mensal_imp.csv"
        )
        
        df = pd.read_csv(caminho_csv)
        df['CO_NCM'] = df['CO_NCM'].astype(str)
        df = df[df['CO_NCM'] == str(ncm)]

        coluna_valor = f"VL_FOB_{tipo}"
        df = df.groupby('DATA')[[coluna_valor]].sum().reset_index()
        df_prophet = df.rename(columns={'DATA': 'ds', coluna_valor: 'y'})
        df_prophet['y'] = df_prophet['y'].fillna(0)

        nome = f"tendencia_vlfob_{tipo.lower()}_ncm{ncm}"

        return self.gerar_profecia(df_prophet, nome, f"Previsão de Valor FOB ({tipo}) - NCM {ncm}", f"Valor FOB {tipo} ($)")
    
    @cache.memoize(timeout=60*60*24)
    def tendencia_vlfob_sh4(self, tipo: Literal['EXP', 'IMP'], sh4: str) -> List[dict]:
        app_logger.info(f"Iniciando análise de tendência de VL_FOB por SH4 {sh4} usando mv_sh4_mensal")

        caminho_csv = "data_pipeline/datasets/dados_agregados/mv_sh4_mensal.csv"
        df = pd.read_csv(caminho_csv)

        df['CO_SH4'] = df['CO_SH4'].astype(str)
        df = df[df['CO_SH4'] == str(sh4)]

        coluna_valor = f"VL_FOB_{tipo}"
        df = df.groupby('DATA')[[coluna_valor]].sum().reset_index()
        df_prophet = df.rename(columns={'DATA': 'ds', coluna_valor: 'y'})
        df_prophet['y'] = df_prophet['y'].fillna(0)

        nome = f"tendencia_vlfob_{tipo.lower()}_sh4{sh4}"

        return self.gerar_profecia(df_prophet, nome, f"Previsão de Valor FOB ({tipo}) - SH4 {sh4}", f"Valor FOB {tipo} ($)")
    
    @cache.memoize(timeout=60*60*24)
    def tendencia_vlfob_setores(self, tipo: Literal['EXP', 'IMP'], setor: str) -> List[dict]:
        app_logger.info(f"Iniciando análise de tendência de VL_FOB por setor '{setor}' usando mv_setores_mensal")

        caminho_csv = "data_pipeline/datasets/dados_agregados/mv_setores_mensal.csv"
        df = pd.read_csv(caminho_csv)

        coluna_valor = f"VL_FOB_{tipo}"
        df = df.groupby('DATA')[[coluna_valor]].sum().reset_index()
        df_prophet = df.rename(columns={'DATA': 'ds', coluna_valor: 'y'})
        df_prophet['y'] = df_prophet['y'].fillna(0)

        nome = f"tendencia_vlfob_{tipo.lower()}_{setor.lower().replace(' ', '_')}"

        return self.gerar_profecia(df_prophet, nome, f"Previsão de Valor FOB ({tipo}) - Setor {setor.title()}", f"Valor FOB {tipo} ($)")

    
    @cache.memoize(timeout=60*60*24)
    def tendencia_ranking_ncm(self, tipo: Literal['EXP', 'IMP']) -> List[dict]:
        caminho = (
            "data_pipeline/datasets/dados_agregados/mv_ncm_mensal_exp.csv"
            if tipo == "EXP" else
            "data_pipeline/datasets/dados_agregados/mv_ncm_mensal_imp.csv"
        )

        df = pd.read_csv(caminho)
        coluna_valor = f'VL_FOB_{tipo}'

        df = df.groupby(['DATA', 'CO_NCM'])[coluna_valor].sum().reset_index()
        df['tipo'] = tipo

        df_resultado = df.groupby(['DATA', 'tipo']).apply(
            lambda x: x.sort_values(coluna_valor, ascending=False).head(10)
        ).reset_index(drop=True)

        return df_resultado.to_dict(orient='records')
    
    @cache.memoize(timeout=60*60*24)
    def tendencia_ranking_sh4(self, tipo: Literal['EXP', 'IMP']) -> List[dict]:
        caminho_csv = "data_pipeline/datasets/dados_agregados/mv_sh4_mensal.csv"
        df = pd.read_csv(caminho_csv)
        coluna_valor = f'VL_FOB_{tipo}'

        df = df.groupby(['DATA', 'CO_SH4'])[coluna_valor].sum().reset_index()
        df['tipo'] = tipo

        df_resultado = df.groupby(['DATA', 'tipo']).apply(
            lambda x: x.sort_values(coluna_valor, ascending=False).head(10)
        ).reset_index(drop=True)

        return df_resultado.to_dict(orient='records')

    # busca os ncm que mais aumentaram/diminuiram exportacao/importacao na série histórica
    @cache.memoize(timeout=60*60*24)
    def maiores_evolucoes_ncm(self, tipo: Literal['EXP', 'IMP']) -> dict:
        caminho = (
            "data_pipeline/datasets/dados_agregados/mv_ncm_mensal_exp.csv"
            if tipo == "EXP" else
            "data_pipeline/datasets/dados_agregados/mv_ncm_mensal_imp.csv"
        )

        df = pd.read_csv(caminho)
        coluna_valor = f'VL_FOB_{tipo}'

        df_pivot = df.groupby(['CO_NCM', 'DATA'])[coluna_valor].sum().unstack().fillna(0)
        variacao = ((df_pivot.iloc[:, -1] - df_pivot.iloc[:, 0]) / df_pivot.iloc[:, 0].replace(0, 1)).sort_values(ascending=False)

        return {
            f"maiores_evolucoes_{tipo.lower()}": variacao.head(10).reset_index().rename(columns={0: "crescimento"}).to_dict(orient='records'),
            f"maiores_reducoes_{tipo.lower()}": variacao.tail(10).reset_index().rename(columns={0: "crescimento"}).to_dict(orient='records'),
        }
    
    # busca os sh4 que mais aumentaram/diminuiram exportacao/importacao na série histórica
    @cache.memoize(timeout=60*60*24)
    def maiores_evolucoes_sh4(self, tipo: Literal['EXP', 'IMP']) -> dict:
        caminho = "data_pipeline/datasets/dados_agregados/mv_sh4_mensal.csv"
        df = pd.read_csv(caminho)
        coluna_valor = f'VL_FOB_{tipo}'

        df_pivot = df.groupby(['CO_SH4', 'DATA'])[coluna_valor].sum().unstack().fillna(0)
        variacao = ((df_pivot.iloc[:, -1] - df_pivot.iloc[:, 0]) / df_pivot.iloc[:, 0].replace(0, 1)).sort_values(ascending=False)

        return {
            f"maiores_evolucoes_{tipo.lower()}": variacao.head(10).reset_index().rename(columns={0: "crescimento"}).to_dict(orient='records'),
            f"maiores_reducoes_{tipo.lower()}": variacao.tail(10).reset_index().rename(columns={0: "crescimento"}).to_dict(orient='records'),
        }