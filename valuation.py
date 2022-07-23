from dataclasses import dataclass
from datetime import timedelta
from sources import FMP
from sources import index_constituents
from sources import treasury_rate_10_yr
from scipy.stats import bootstrap
from scipy.stats import linregress
from scipy.stats import t
import numpy as np
import pandas as pd

fmp = FMP()

treasury_rate = treasury_rate_10_yr()
projection_years = 10


@dataclass
class GrowthEstimate:
    low: float
    high: float
    expected_growth_rate: float


@dataclass
class IntrinsicValue:
    low_valuation: float
    high_valuation: float
    enterprise_value: float
    expected_growth_rate: float


@dataclass
class ProjectedCashflows:
    low_projection: pd.Series
    high_projection: pd.Series


def estimate_growth(annualized_fcf: pd.Series, confidence_level=0.5):
    pct_change = annualized_fcf.pct_change()
    est = bootstrap((pct_change.dropna(),), np.mean, confidence_level=confidence_level)
    expected_growth_rate = annualized_fcf.pct_change().dropna().mean()
    expected_growth_rate = min(expected_growth_rate, annualized_fcf.pct_change().dropna().iloc[-1])
    return GrowthEstimate(est.confidence_interval.low, est.confidence_interval.high, expected_growth_rate)


def intrinsic_value(latest_fcf, fcf_growth_rate):
    value = 0.0
    for year in range(1, projection_years + 1):
        weight = (1 + fcf_growth_rate) / (1 + treasury_rate)
        value = value + latest_fcf * weight ** year
    return value


def annualize_fcf(quarterly_fcf):
    if len(quarterly_fcf) % 4 != 0:
        quarterly_fcf = quarterly_fcf[0:(len(quarterly_fcf) // 4) * 4]
    annualized = quarterly_fcf.groupby(quarterly_fcf.index // 4).sum()
    return annualized.loc[::-1].reset_index(drop=True)


def value_asset_linear_regression(enterprise_value: float, annualized_fcf: pd.Series, confidence_level: float=0.5):
    lr = linregress(annualized_fcf.index, annualized_fcf)
    ts = abs(t.ppf((1 - confidence_level) / 2, len(annualized_fcf) - 2))
    slope_low = lr.slope - ts * lr.stderr
    slope_high = lr.slope + ts * lr.stderr
    intercept_low = lr.intercept - ts * lr.intercept_stderr
    intercept_high = lr.intercept + ts * lr.intercept_stderr
    low_valuation = 0.0
    high_valuation = 0.0
    base_index = annualized_fcf.index.max()
    for year in range(1, projection_years + 1):
        i = base_index + year
        low_valuation += max(intercept_low + slope_low * i, 0)
        high_valuation += max(intercept_high + slope_high * i, 0)
    if lr.slope < 0 and annualized_fcf.iloc[-1] <= 0.00001:
        expected_growth_rate = -1.0
    elif annualized_fcf.iloc[-1] < 0.00001:
        expected_growth_rate = 1.0
    else:
        terminal = max((lr.intercept + lr.slope * (base_index + projection_years)), 0)
        expected_growth_rate = (terminal / annualized_fcf.iloc[-1])**(1/projection_years) - 1
    return IntrinsicValue(low_valuation, high_valuation, enterprise_value, expected_growth_rate)


def value_asset(enterprise_value, quarterly_fcf):
    if len(quarterly_fcf) < 4:
        return IntrinsicValue(enterprise_value, enterprise_value, enterprise_value, 0.0)
    annualized_fcf = annualize_fcf(quarterly_fcf)
    if annualized_fcf.min() < 0 or annualized_fcf.pct_change().max() >= 9.0:
        return value_asset_linear_regression(enterprise_value, annualized_fcf)
    growth_estimate = estimate_growth(annualized_fcf)
    low_value = intrinsic_value(annualized_fcf.iloc[-1], growth_estimate.low)
    high_value = intrinsic_value(annualized_fcf.iloc[-1], growth_estimate.high)
    expected_growth_rate = growth_estimate.expected_growth_rate
    return IntrinsicValue(low_value, high_value, enterprise_value, expected_growth_rate)


def adjusted_freecashflow(ocf_series, capex_series):
    weights = ocf_series / ocf_series.sum()
    adjusted_capex = capex_series.sum() * weights
    return ocf_series - adjusted_capex


def value_stock(ticker):
    enterprise_value = fmp.enterprise_value(ticker)
    historic_cashflow = fmp.historic_cashflow(ticker)
    quarterly_fcf = adjusted_freecashflow(historic_cashflow.operating_cashflow, historic_cashflow.capex)
    return value_asset(enterprise_value, quarterly_fcf)


def etf_fcf(constituents):
    years = 5
    quarters = years * 4
    fcf = pd.Series([0.0] * quarters)
    for stock in constituents:
        stock_fcf = fmp.historic_cashflow(stock).free_cashflow
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
