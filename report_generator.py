from datetime import datetime
import pandas as pd
import sources
import valuation

reports_dir = "/Users/acataldo/Code/finance/financy/reports"

def sp_500_report():
    stocks = sources.index_constituents('SPX')
    buy_hold_sell = ([], [], [])
    for stock in stocks[0:10]:
        iv = valuation.value_stock(stock)
        ba = sources.bid_ask(stock)
        liquidity = 1 - (ba.ask - ba.bid)/ba.ask
        if iv.market_cap < iv.low_valuation:
            undervalued_by = (iv.low_valuation - iv.market_cap) / (iv.high_valuation - iv.low_valuation)
            rating = undervalued_by + iv.expected_growth_rate
            buy_hold_sell[0].append((stock, rating))
        elif iv.market_cap > iv.high_valuation:
            overvalued_by = (iv.market_cap - iv.low_valuation) / (iv.high_valuation - iv.low_valuation)
            rating = overvalued_by - iv.expected_growth_rate
            buy_hold_sell[2].append((stock, rating))
        else:
            buy_hold_sell[1].append(stock)
    buy = pd.DataFrame(buy_hold_sell[0], columns=['ticker', 'undervalued_rating'])
    buy.sort_values('undervalued_rating', ascending=False, ignore_index=True)
    hold = pd.DataFrame(buy_hold_sell[1], columns=['ticker'])
    hold.sort_values('ticker', ignore_index=True)
    sell = pd.DataFrame(buy_hold_sell[2], columns=['ticker', 'undervalued_rating'])
    sell.sort_values('undervalued_rating', ascending=False, ignore_index=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")
    buy.to_csv(f"{reports_dir}/buy_sp500_{timestamp}.csv", index=False)
    hold.to_csv(f"{reports_dir}/hold_sp500_{timestamp}.csv", index=False)
    sell.to_csv(f"{reports_dir}/sell_sp500_{timestamp}.csv", index=False)
