from datetime import datetime
import config
import logging
import pandas as pd
import sources
import traceback
import valuation

reports_dir = config.reports_dir

BUY = 0
HOLD = 1
SELL = 2


def rate_stock(iv, ba, stock):
    if ba.ask == 0.0 or ba.bid == 0.0:
        illiquidity = 0.5
        logging.warning(f"{stock} had unexpected bid-ask values: {ba}")
    else:
        illiquidity = (ba.ask - ba.bid) / ba.ask
    if iv.enterprise_value < iv.low_valuation:
        valuation_growth = iv.enterprise_value / iv.low_valuation
        rating = ((1 + iv.expected_growth_rate) ** 10 * (valuation_growth - illiquidity)) ** (1 / 10) - 1
        return (BUY, (stock,
                      rating,
                      iv.expected_growth_rate,
                      iv.enterprise_value,
                      iv.low_valuation,
                      iv.high_valuation,
                      1 - illiquidity))
    elif iv.enterprise_value > iv.high_valuation:
        valuation_shrinkage = iv.high_valuation / iv.enterprise_value
        rating = ((1 + iv.expected_growth_rate) ** 10 * (valuation_shrinkage - illiquidity)) ** (1 / 10) - 1
        return (SELL, (stock,
                       rating,
                       iv.expected_growth_rate,
                       iv.enterprise_value,
                       iv.low_valuation,
                       iv.high_valuation,
                       1 - illiquidity))
    else:
        return HOLD, stock


def _rate_stock(buy_hold_sell, stock, liq):
    try:
        iv = valuation.value_stock(stock)
        ba = liq.bid_ask(stock)
        rating = rate_stock(iv, ba, stock)
        buy_hold_sell[rating[0]].append(rating[1])
    except Exception as err:
        logging.error(f"Unexpected error on {stock}")
        logging.error(traceback.format_exc())
        buy_hold_sell[3].append(stock)


def sp_500_report():
    stocks = sources.index_constituents('SPX')
    buy_hold_sell = ([], [], [], [])
    with sources.Liquidity() as liq:
        for stock in stocks:
            _rate_stock(buy_hold_sell, stock, liq)
    buy_columns = ['ticker',
                   'undervalued_rating',
                   'fcf_growth_rate',
                   'enterprise_value',
                   'low_valuation',
                   'high_valuation',
                   'liquidity']
    buy = pd.DataFrame(buy_hold_sell[0], columns=buy_columns)
    buy.sort_values('undervalued_rating', ascending=False, ignore_index=True, inplace=True)
    hold = pd.DataFrame(buy_hold_sell[1], columns=['ticker'])
    hold.sort_values('ticker', ignore_index=True, inplace=True)
    sell_columns = ['ticker',
                    'overvalued_rating',
                    'fcf_growth_rate',
                    'enterprise_value',
                    'low_valuation',
                    'high_valuation',
                    'liquidity']
    sell = pd.DataFrame(buy_hold_sell[2], columns=sell_columns)
    sell.sort_values('overvalued_rating', ascending=False, ignore_index=True, inplace=True)
    errors = pd.DataFrame(buy_hold_sell[3], columns=['ticker'])
    errors.sort_values('ticker', ignore_index=True, inplace=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")
    buy.to_csv(f"{reports_dir}/buy_sp500_{timestamp}.csv", index=False)
    hold.to_csv(f"{reports_dir}/hold_sp500_{timestamp}.csv", index=False)
    sell.to_csv(f"{reports_dir}/sell_sp500_{timestamp}.csv", index=False)
    errors.to_csv(f"{reports_dir}/errors_sp500_{timestamp}.csv", index=False)
