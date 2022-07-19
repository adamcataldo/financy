from collections import namedtuple
from datetime import timedelta
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

GrowthEstimate = namedtuple('GrowthEstimate', ['low', 'high', 'expected_growth_rate'])


class DataQualityError(Exception):

    def __init__(self, message="DataQuality Error"):
        self.message = message
        super().__init__(self.message)


def estimate_growth(quarterly_fcf, confidence_level=0.5):
    annualized_fcf = annualize_fcf(quarterly_fcf)
    if quarterly_fcf.min() < 0:
        return estimate_growth_negative_fcf(annualized_fcf, confidence_level=confidence_level)
    pct_change = annualized_fcf.pct_change()
    est = bootstrap((pct_change.dropna(),), np.mean, confidence_level=confidence_level)
    expected_growth_rate = annualized_fcf.pct_change().dropna().mean()
    expected_growth_rate = min(expected_growth_rate, annualized_fcf.pct_change().dropna().iloc[-1])
    return GrowthEstimate(est.confidence_interval.low, est.confidence_interval.high, expected_growth_rate)


def estimate_growth_negative_fcf(fcf, confidence_level=0.5):
    raise Exception("Not dealing with negative growth right now.")
    lr = linregress(fcf.index, fcf)
    ts = abs(t.ppf((1 - confidence_level) / 2, len(fcf) - 2))
    slope_low = lr.slope - ts * lr.stderr
    slope_high = lr.slope + ts * lr.stderr
    intercept_low = lr.intercept - ts * lr.intercept_stderr
    intercept_high = lr.intercept + ts * lr.intercept_stderr
    next_low = intercept_low + slope_low * (fcf.index.max() + 1)
    next_high = intercept_high + slope_high * (fcf.index.max() + 1)
    next_expected = lr.intercept + lr.slope * (fcf.index.max() + 1)
    latest = fcf[len(fcf) - 1]
    growth_low = (next_low - latest) / abs(latest)
    growth_high = (next_high - latest) / abs(latest)
    growth_expected = (next_expected - latest) / abs(latest)
    return GrowthEstimate(growth_low, growth_high, growth_expected)


def intrinsic_value(latest_fcf, fcf_growth_rate):
    years = 10
    value = 0.0
    for year in range(1, years + 1):
        weight = (1 + fcf_growth_rate) / (1 + treasury_rate)
        value = value + latest_fcf * weight ** year
    return value


def annualize_fcf(quarterly_fcf):
    annualized = quarterly_fcf.groupby(quarterly_fcf.index // 4).sum()
    return annualized.loc[::-1].reset_index(drop=True)


def value_asset(enterprise_value, quarterly_fcf):
    growth_estimate = estimate_growth(quarterly_fcf)
    annualized_fcf = annualize_fcf(quarterly_fcf)
    low_value = intrinsic_value(annualized_fcf.iloc[-1], growth_estimate.low)
    high_value = intrinsic_value(annualized_fcf.iloc[-1], growth_estimate.high)
    expected_growth_rate = growth_estimate.expected_growth_rate
    IntrinsicValue = namedtuple('IntrinsicValue',
                                ['low_valuation', 'high_valuation', 'enterprise_value', 'expected_growth_rate'])
    return IntrinsicValue(low_value, high_value, enterprise_value, expected_growth_rate)


def quarter_statement_date_dq(dates):
    x = -dates.diff().max()
    if x < timedelta(days=88):
        raise DataQualityError(f"Found two quarters seperated by only {x.days} days")


def value_stock(ticker):
    enterprise_value = fmp.enterprise_value(ticker)
    quarterly_fcf = fmp.historic_fcf(ticker)
    quarter_statement_date_dq(quarterly_fcf.quarter)
    quarterly_fcf = quarterly_fcf.free_cashflow
    return value_asset(enterprise_value, quarterly_fcf)


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
            stock_fcf = pd.concat([stock_fcf, zero_pad], ignore_index=True)
        fcf += stock_fcf
    return fcf


def etf_market_cap(constituents):
    market_cap = 0.0
    for stock in constituents:
        stock_market_cap = fmp.market_cap(stock)
        market_cap += stock_market_cap
    return market_cap


def value_etf(index):
    # FIXME: Change market cap to enterprise value
    constituents = index_constituents(index)
    market_cap = etf_market_cap(constituents)
    quarterly_fcf = etf_fcf(constituents)
    return value_asset(market_cap, quarterly_fcf)
