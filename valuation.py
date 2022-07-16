from collections import namedtuple
from sources import FMP
from sources import index_constituents
from sources import treasury_rate_10_yr
from scipy.stats import bootstrap
from scipy.stats import linregress
from scipy.stats import t
import numpy as np
import pandas as pd

this_dir = "/Users/acataldo/Code/finance/financy"
data_dir = f"{this_dir}/data"

fmp = FMP(this_dir)

treasury_rate = treasury_rate_10_yr()

def estimate_growth(fcf, confidence_level=0.5):
    if (fcf.min() < 0):
        return estimate_growth_negative_fcf(fcf, confidence_level=confidence_level)
    pct_change = fcf.pct_change()
    est = bootstrap((pct_change.dropna(),), np.mean, confidence_level=confidence_level)
    GrowthEstimate = namedtuple('GrowthEstimate', ['low', 'high'])
    return GrowthEstimate(est.confidence_interval.low, est.confidence_interval.high)

def estimate_growth_negative_fcf(fcf, confidence_level=0.5):
    lr = linregress(fcf.index, fcf)
    ts = abs(t.ppf((1 - confidence_level)/2, len(fcf) - 2))
    slope_low = lr.slope - ts*lr.stderr
    slope_high = lr.slope + ts*lr.stderr
    latest = fcf[len(fcf)-1]
    GrowthEstimate = namedtuple('GrowthEstimate', ['low', 'high'])
    return GrowthEstimate(slope_low / latest, slope_high / latest)

def intrinsic_value(latest_fcf, fcf_growth_rate):
    years = 10
    value = 0.0
    for year in range(1, years+1):
        weight = (1 + fcf_growth_rate) / (1 + treasury_rate)
        value = value + latest_fcf * weight**year
    return value

def annualize_fcf(quarterly_fcf):
    annualized = quarterly_fcf.groupby(quarterly_fcf.index // 4).sum()
    return annualized.loc[::-1].reset_index(drop=True)

def value_asset(market_cap, quarterly_fcf):
    annualized_fcf = annualize_fcf(quarterly_fcf)
    growth_estimate = estimate_growth(annualized_fcf)
    low_value = intrinsic_value(annualized_fcf.iloc[-1], growth_estimate.low)
    high_value = intrinsic_value(annualized_fcf.iloc[-1], growth_estimate.high)
    IntrinsicValue = namedtuple('IntrinsicValue', ['low_valuation', 'high_valuation', 'market_cap'])
    return IntrinsicValue(low_value, high_value, market_cap)
    
def value_stock(ticker):
    market_cap = fmp.market_cap(ticker)
    quarterly_fcf = fmp.historic_fcf(ticker).free_cashflow    
    return value_asset(market_cap, quarterly_fcf)

def etf_fcf(constituents):
    years = 5
    quarters = years * 4
    fcf = pd.Series([0.0] * quarters)
    for stock in constituents:
        stock_fcf = fmp.historic_fcf(stock).free_cashflow
        if len(stock_fcf) > quarters:
            stock_fcf = stock_fcf[0:quarters]
        if len(stock_fcf) < quarters:
            zero_pad = pd.Series([0.0] * (quarters - len(stock_fcf)))
            stock_fcf = pd.concat([stock_fcf, zero_pad], ignore_index = True)
        fcf += stock_fcf
    return fcf

def etf_market_cap(constituents):
    market_cap = 0.0
    for stock in constituents:
        stock_market_cap = fmp.market_cap(stock)
        market_cap += stock_market_cap
    return market_cap

def value_etf(index):
    constituents = index_constituents(index)
    market_cap = etf_market_cap(constituents)
    quarterly_fcf = etf_fcf(constituents)
    return value_asset(market_cap, quarterly_fcf)
