from collections import namedtuple
from scipy.stats import bootstrap
from scipy.stats import linregress
from scipy.stats import t
import numpy as np
import pandas as pd

# Assumes file is in a csv file, named "{path}/{ticker}_quarterly_cash-flow.csv"
# Assume Yahoo Finance Plus format, for quarterly cash flow data
# Returns estimate in $BB
def value_csv(ticker, path = "/Users/acataldo/Code/finance/FCF_analysis/data"):
    annualized = extract_annualized(ticker, path)
    growth_estimate = estimate_growth(annualized)
    low_value = intrinsic_value(annualized.free_cashflow.iloc[-1], growth_estimate.low) / 1e9
    high_value = intrinsic_value(annualized.free_cashflow.iloc[-1], growth_estimate.high) / 1e9
    IntrinsicValue = namedtuple('IntrinsicValue', ['low', 'high'])
    return IntrinsicValue(low_value, high_value)

def extract_annualized(ticker, path = "/Users/acataldo/Code/finance/FCF_analysis/data"):
    df = pd.read_csv(f"{path}/{ticker}_quarterly_cash-flow.csv")
    row = df[df.name == "FreeCashFlow"]
    formatted = row.transpose()[2:]
    formatted.reset_index(inplace=True)
    formatted.columns = ['quarter', 'free_cashflow']
    formatted.quarter = pd.to_datetime(formatted.quarter, format = '%m/%d/%Y')
    formatted.free_cashflow = formatted.replace(',','', regex=True).free_cashflow.astype(float)
    annualized = formatted.groupby(formatted.index // 4).agg({'quarter':'max', 'free_cashflow':'sum'})
    annualized.rename(columns = {'quarter':'year_ending'}, inplace = True)
    last_five_years = annualized[0:5]
    return last_five_years.sort_values('year_ending', ignore_index=True)
    
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


#Look into https://fmpcloud.io/plans