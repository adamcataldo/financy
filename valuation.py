from collections import namedtuple
from datetime import datetime
from fmp_data import FMPData
from scipy.stats import bootstrap
from scipy.stats import linregress
from scipy.stats import t
from wikipedia_data import sp_500_constituents
import numpy as np
import pandas as pd

this_dir = "/Users/acataldo/Code/finance/financy"
data_dir = f"{this_dir}/data"

fmp = FMPData(this_dir)

def estimate_growth(fcf_dataframe, confidence_level=0.5):
    df = fcf_dataframe.copy()
    if (df.free_cashflow.min() < 0):
        return estimate_growth_negative_fcf(df, confidence_level=0.5)
    df['fcf_pct_change'] = df.free_cashflow.pct_change()
    est = bootstrap((df.fcf_pct_change.dropna(),), np.mean, confidence_level=confidence_level)
    GrowthEstimate = namedtuple('GrowthEstimate', ['low', 'high'])
    return GrowthEstimate(est.confidence_interval.low, est.confidence_interval.high)

def estimate_growth_negative_fcf(df, confidence_level=0.5):
    lr = linregress(df.index, df.free_cashflow)
    ts = abs(t.ppf((1 - confidence_level)/2, len(df.free_cashflow) - 2))
    slope_low = lr.slope - ts*lr.stderr
    slope_high = lr.slope + ts*lr.stderr
    latest = df.free_cashflow[len(df.free_cashflow)-1]
    GrowthEstimate = namedtuple('GrowthEstimate', ['low', 'high'])
    return GrowthEstimate(slope_low / latest, slope_high / latest)

def intrinsic_value(latest_fcf, fcf_growth_rate, treasury_rate = 0.0308):
    years = 10
    value = 0.0
    for year in range(1, years+1):
        weight = (1 + fcf_growth_rate) / (1 + treasury_rate)
        value = value + latest_fcf * weight**year
    return value

def annualize_fcf(quarterly_fcf_df):
    annualized = quarterly_fcf_df.groupby(quarterly_fcf_df.index // 4).agg({'free_cashflow':'sum'})
    return annualized.loc[::-1].reset_index(drop=True)

def value_asset(market_cap, quarterly_fcf):
    annualized_fcf = annualize_fcf(quarterly_fcf)
    growth_estimate = estimate_growth(annualized_fcf)
    low_value = intrinsic_value(annualized_fcf.free_cashflow.iloc[-1], growth_estimate.low)
    high_value = intrinsic_value(annualized_fcf.free_cashflow.iloc[-1], growth_estimate.high)
    IntrinsicValue = namedtuple('IntrinsicValue', ['low_valuation', 'high_valuation', 'market_cap'])
    return IntrinsicValue(low_value, high_value, market_cap)
    
def value_stock(ticker):
    market_cap = fmp.market_cap(ticker)
    quarterly_fcf = fmp.historic_fcf(ticker).free_cashflow    
    return value_asset(market_cap, quarterly_fcf)

def sp_500_fcf():
    years = 5
    quarters = years * 4
    constituents = sp_500_constituents()
    fcf = pd.Series([0.0] * quarters)
    for stock in constituents:
        stock_fcf = fmp.historic_fcf(stock).free_cashflow
        if len(stock_fcf) > quarters:
            stock_fcf = stock_fcf[0:quarters]
        if len(stock_fcf) < quarters:
            zero_pad = pd.Series([0.0] * (quarters - len(stock_fcf)))
            stock_fcf = pd.concat([stock_fcf, zero_pad], ignore_index = True)
        fcf += stock_fcf
    return pd.DataFrame(fcf, columns=['free_cashflow'])

def sp_500_market_cap():
    constituents = sp_500_constituents()
    market_cap = 0.0
    for stock in constituents:
        stock_market_cap = fmp.market_cap(stock)
        market_cap += stock_market_cap
    return market_cap

def value_sp_500():
    market_cap = sp_500_market_cap()
    quarterly_fcf = sp_500_fcf()
    return value_asset(market_cap, quarterly_fcf)
