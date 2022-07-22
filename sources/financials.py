from datetime import datetime
from executor import RetryingExecutor
import config
import fmpsdk as fmp
import logging
import pandas as pd

api_calls_per_minute = config.fmp_api_calls_per_minute


class FMP:
    def __init__(self):
        self.apikey = config.fmp_apikey
        self.executor = RetryingExecutor(api_calls_per_minute)
        logger = logging.getLogger()
        handler = logging.FileHandler(filename=config.fmp_log, mode='w')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def market_cap(self, symbol):
        symbol = symbol.replace(".", "-")
        query = lambda: fmp.company_profile(apikey=self.apikey, symbol=symbol)
        logging.info(f"fetched market cap for {symbol}")
        value = self.executor.execute(query)
        return value[0]['mktCap']

    def enterprise_value(self, symbol):
        symbol = symbol.replace(".", "-")
        query = lambda: fmp.balance_sheet_statement(apikey=self.apikey, symbol=symbol, period="quarter", limit=1)
        balance_sheet = self.executor.execute(query)[0]
        logging.info(f"fetched balance_sheet for {symbol}")
        debt = balance_sheet['totalDebt']
        cash = balance_sheet['cashAndCashEquivalents']
        market_cap = self.market_cap(symbol)
        return market_cap + debt - cash

    # Period in ["annual", "quarter"]
    def historic_cashflow(self, symbol, period="quarter", limit=20):
        symbol = symbol.replace(".", "-")
        query = lambda: fmp.cash_flow_statement(apikey=self.apikey, symbol=symbol, period=period, limit=20)
        logging.info(f"fetched historic FCF for {symbol}")
        statements = self.executor.execute(query)
        data = [(datetime.strptime(x['date'], '%Y-%m-%d'),
                 x['freeCashFlow'],
                 x['capitalExpenditure'],
                 x['operatingCashFlow']) for x in statements]
        return pd.DataFrame(data, columns=[period,
                                           'free_cashflow',
                                           'capex',
                                           'operating_cashflow'])

    def historic_ocf(self, symbol, period="quarter", limit=20):
        symbol = symbol.replace(".", "-")
        query = lambda: fmp.cash_flow_statement(apikey=self.apikey, symbol=symbol, period=period, limit=20)
        logging.info(f"fetched historic FCF for {symbol}")
        statements = self.executor.execute(query)
        data = [(datetime.strptime(x['date'], '%Y-%m-%d'), x['operatingCashFlow']) for x in statements]
        return pd.DataFrame(data, columns=[period, 'operating_cashflow'])
