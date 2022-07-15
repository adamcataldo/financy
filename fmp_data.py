from executor import RetryingExecutor
import fmpsdk as fmp
import logging
import pandas as pd

api_calls_per_minute = 300

class FMPData:
    def __init__(self, this_dir):
        with open(f"{this_dir}/.apikey") as f:
            self.apikey = f.read().strip()
        self.executor = RetryingExecutor(api_calls_per_minute)
        logger = logging.getLogger()
        handler = logging.FileHandler(filename=f"{this_dir}/logs/fmp.log", mode='a')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    # Source https://fmpcloud.io/
    def market_cap(self, symbol):
        symbol = symbol.replace(".", "-")
        query = lambda : fmp.company_profile(apikey=self.apikey, symbol=symbol)
        logging.info(f"fetched market cap for {symbol}")
        value = self.executor.execute(query)
        return value[0]['mktCap']

    # Source https://fmpcloud.io/
    # Period in ["annual", "quarter"]
    def historic_fcf(self, symbol, period="quarter", limit=20):
        symbol = symbol.replace(".", "-")
        query = lambda : fmp.cash_flow_statement(apikey=self.apikey, symbol=symbol, period=period, limit=20)
        logging.info(f"fetched historic FCF for {symbol}")
        statements = self.executor.execute(query)
        data = [(x['date'], x['freeCashFlow']) for x in statements]
        return pd.DataFrame(data, columns=[period, 'free_cashflow'])
