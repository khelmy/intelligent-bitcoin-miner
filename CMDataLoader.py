import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LinearRegression
from datetime import date
from functools import lru_cache

# Note: pagination not implemented, so don't set lookbacks > 10,000 (>27 years)
class CMDataLoader:
    @staticmethod
    @lru_cache
    def __get_network_data(metrics: list = ['HashRate', 'IssTotUSD', 'FeeTotUSD', 'PriceUSD', 'FeeMeanNtv'], end_time: str = date.today().strftime('%Y-%m-%d')):
        api_str = f"https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets=btc&metrics={','.join(metrics)}&end_time={end_time}&page_size=10000&pretty=true"
        response = requests.get(api_str).json()
        return pd.DataFrame(response['data'])

    # Returns last lookback days of hash rate, from lookback_date
    @staticmethod
    @lru_cache
    def get_historical_hash_rate(lookback: int = 30, lookback_date: str = date.today().strftime('%Y-%m-%d')):
        return pd.to_numeric(CMDataLoader.__get_network_data(end_time = lookback_date).HashRate.tail(lookback)).reset_index(drop = True)

    # Returns last lookback days of USD miner revenue, from lookback_date
    @staticmethod
    @lru_cache
    def get_historical_miner_revenue_usd(lookback: int = 30, lookback_date: str = date.today().strftime('%Y-%m-%d')):
        values = CMDataLoader.__get_network_data(end_time = lookback_date)
        return (pd.to_numeric(values.IssTotUSD) + pd.to_numeric(values.FeeTotUSD)).tail(lookback).reset_index(drop = True)

    # Returns current price, drift, standard error
    # Drift, SE calculated in log-space
    @staticmethod
    @lru_cache
    def get_historical_price_params(lookback: int = 100, lookback_date: str = date.today().strftime('%Y-%m-%d')):
        values = pd.to_numeric(CMDataLoader.__get_network_data(end_time = lookback_date).PriceUSD.tail(lookback))
        x = np.arange(values.size)
        model = LinearRegression().fit(x.reshape((-1, 1)), np.log(values))

        current_price, drift, se = (values.iloc[-1], model.coef_[0], (np.log(values) - model.intercept_ - (x * model.coef_)).std())
        return (current_price, drift, se)

    # Returns (mean, sigma) over normal fee dist
    @staticmethod
    @lru_cache
    def get_historical_fee_params(lookback: int = 100, lookback_date: str = date.today().strftime('%Y-%m-%d')):
        values = pd.to_numeric(CMDataLoader.__get_network_data(end_time = lookback_date).FeeMeanNtv.tail(lookback))
        mean, sigma = (values.mean(), values.std())
        return (mean, sigma)
