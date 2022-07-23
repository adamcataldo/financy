from datetime import datetime
import config
import logging
import pandas as pd
import sources
import traceback
import valuation
import warnings

reports_dir = config.reports_dir

BUY = 0
HOLD = 1
SELL = 2
ERROR = 3


def rate_stock(iv, stock):
    if iv.enterprise_value < iv.low_valuation:
        if iv.low_valuation <= 0 or iv.enterprise_value < 0:
            valuation_growth = 1.0
        else:
            valuation_growth = iv.enterprise_value / iv.low_valuation
        rating = ((1 + iv.expected_growth_rate) ** 10 * valuation_growth) ** (1 / 10) - 1
        return (BUY, (stock,
                      rating,
                      iv.expected_growth_rate,
                      iv.enterprise_value,
                      iv.low_valuation,
                      iv.high_valuation))
    elif iv.enterprise_value > iv.high_valuation:
        valuation_shrinkage = iv.high_valuation / iv.enterprise_value
        rating = ((1 + iv.expected_growth_rate) ** 10 * valuation_shrinkage) ** (1 / 10) - 1
        return (SELL, (stock,
                       rating,
                       iv.expected_growth_rate,
                       iv.enterprise_value,
                       iv.low_valuation,
                       iv.high_valuation))
    else:
        return HOLD, stock


def _rate_stock(stock):
    try:
        warnings.filterwarnings("error")
        iv = valuation.value_stock(stock)
        rating = rate_stock(iv, stock)
        warnings.resetwarnings()
        return rating
    except RuntimeWarning as rw:
        logging.error(f"Unexpected warning on {stock}")
        logging.error(traceback.format_exc())
        return ERROR, stock
    except Exception as err:
        logging.error(f"Unexpected error on {stock}")
        logging.error(traceback.format_exc())
        return ERROR, stock


def sp_500_report():
    stocks = sources.index_constituents('SPX')
    buy_hold_sell = ([], [], [], [])
    for stock in stocks:
        rating = _rate_stock(stock)
        buy_hold_sell[rating[0]].append(rating[1])
    buy_columns = ['ticker',
                   'undervalued_rating',
                   'fcf_growth_rate',
                   'enterprise_value',
                   'low_valuation',
                   'high_valuation']
    buy = pd.DataFrame(buy_hold_sell[0], columns=buy_columns)
    buy.sort_values('undervalued_rating', ascending=False, ignore_index=True, inplace=True)
    hold = pd.DataFrame(buy_hold_sell[1], columns=['ticker'])
    hold.sort_values('ticker', ignore_index=True, inplace=True)
    sell_columns = ['ticker',
                    'overvalued_rating',
                    'fcf_growth_rate',
                    'enterprise_value',
                    'low_valuation',
                    'high_valuation']
    sell = pd.DataFrame(buy_hold_sell[2], columns=sell_columns)
    sell.sort_values('overvalued_rating', ascending=False, ignore_index=True, inplace=True)
    errors = pd.DataFrame(buy_hold_sell[3], columns=['ticker'])
    errors.sort_values('ticker', ignore_index=True, inplace=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")
    buy.to_csv(f"{reports_dir}/buy_sp500_{timestamp}.csv", index=False)
    hold.to_csv(f"{reports_dir}/hold_sp500_{timestamp}.csv", index=False)
    sell.to_csv(f"{reports_dir}/sell_sp500_{timestamp}.csv", index=False)
    errors.to_csv(f"{reports_dir}/errors_sp500_{timestamp}.csv", index=False)
