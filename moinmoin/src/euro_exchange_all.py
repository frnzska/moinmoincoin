"""
a = EuroExchangeAll.execute(curr_shares=[('ETH', 1.0), ('BTC', 1.0)], start='2017-12-20')      
"""
import pandas as pd
import datetime as dt
import calendar
from typing import List
import requests
import json
from collections import namedtuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EuroExchangeAll:

    def __init__(self, *, curr_shares:List, start:str, end:str, period:int):
        """
        :param self: 
        :param curr_shares: 
        """
        CurrencyShare = namedtuple('CurrencyShare', ['curr', 'share'], verbose=False)
        self.curr_shares = [CurrencyShare(*x) for x in curr_shares]
        self.start_time = calendar.timegm(dt.datetime.strptime(start, '%Y-%m-%d').utctimetuple())
        self.end_time = calendar.timegm(dt.datetime.strptime(end, '%Y-%m-%d').utctimetuple())
        self.period = period # just daily seems possible
        self.eur_factor = -1.0
        self.exchange_data = None


    @classmethod
    def execute(cls, *, curr_shares:List, start:str, end:str=dt.datetime.now().strftime('%Y-%m-%d'), period=86400):
        """
        Exchange values for given currencies in euro.
        :param curr_shares: List of currency-share tuples 
        :param start: start date format 'YYYY-mm-dd'
        :param end:  end date format 'YYYY-mm-dd'
        """
        c = cls(curr_shares=curr_shares, start=start, end=end, period=period)
        return c.get_euro_factor().get_exchange_data()


    def get_euro_factor(self):
        url = "http://api.fixer.io/latest?symbols=USD"
        res = json.loads(requests.get(url).text)["rates"]["USD"]
        self.eur_factor = res
        return self

    def get_poloniex_df(self, currency:str, share:str):
        url = f'https://poloniex.com/public?command=returnChartData&currencyPair=USDT_{currency}&start={self.start_time}&end={self.end_time}&period={self.period}'
        print(url)
        df = pd.read_json(url)

        def _add_euro(df):
            df['weightedAverageEur'] =  df['weightedAverage'] / self.eur_factor
            return df

        def _add_shares(df):
            df['wAvgEurShares'] = df['weightedAverageEur'] * share
            return df

        df = _add_euro(df)
        df = _add_shares(df)
        print(df)
        return df

    def get_exchange_data(self):
        exchange_data = dict()
        for elem in self.curr_shares:
            exchange_data[elem.curr] = self.get_poloniex_df(*elem)
        self.exchange_data = exchange_data
        return self
