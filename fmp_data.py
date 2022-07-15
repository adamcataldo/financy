from executor import Executor
import fmpsdk as fmp
import pandas as pd

api_calls_per_minute = 300

class FMPData:
    def __init__(self, this_dir):
        with open(f"{this_dir}/.apikey") as f:
            self.apikey = f.read().strip()
        self.executor = Executor(api_calls_per_minute)
    
    # Source https://fmpcloud.io/
    def market_cap(self, symbol):
        query = lambda : fmp.company_profile(apikey=self.apikey, symbol=symbol)
        value = self.executor.execute(query)
        return value[0]['mktCap']

    # Source https://fmpcloud.io/
    # Period in ["annual", "quarter"]
    def historic_fcf(self, symbol, period="quarter"):
        query = lambda : fmp.cash_flow_statement(apikey=self.apikey, symbol=symbol, period=period)
        statements = self.executor.execute(query)
        data = [(x['date'], x['freeCashFlow']) for x in statements]
        return pd.DataFrame(data, columns=[period, 'free_cashflow'])
