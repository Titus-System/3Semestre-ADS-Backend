import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from pandas.tseries.offsets import MonthEnd
import warnings

from app.utils.logging_config import app_logger, error_logger


warnings.filterwarnings("ignore")


class Vidente():

    def gerar_profecia_json(self, df_prophet: pd.DataFrame, n_periods:int = 24):
        try : 
            if len(df_prophet) < 2:
                app_logger.info("Dados insuficientes para modelagem.")
                return [{"ds":"2014-01-01", "yhat":0}]

            df = df_prophet.copy()
            df['ds'] = pd.to_datetime(df['ds'])
            df.set_index('ds', inplace=True)
            df = df.asfreq('MS')  #frequência mensal com início no início do mês
            df['y'] = df['y'].interpolate() 

            modelo = SARIMAX(df['y'], order=(1,1,1), seasonal_order=(1,1,0,12), enforce_stationarity=False, enforce_invertibility=False)
            modelo_fit = modelo.fit(disp=False)

            future_index = pd.date_range(start=df.index[-1] + MonthEnd(1), periods=n_periods, freq='MS')
            previsoes = modelo_fit.forecast(steps=n_periods)

            df_previsao = pd.concat([df['y'], pd.Series(previsoes, index=future_index)], axis=0)

            resultado = df_previsao.reset_index()
            resultado.columns = ['ds', 'yhat']
            resultado['ds'] = resultado['ds'].astype(str)

            app_logger.info(f"Análise de tendências finalizada")
            return resultado.to_dict(orient='records')
        except Exception as e:
            error_logger.error(f"Erro ao gerar previsão de tendência: {str(e)}")
            return None