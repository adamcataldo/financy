import pandas as pd


# From marketwatch
def treasury_rate_10_yr():
    tables = pd.read_html("https://www.marketwatch.com/investing/bond/tmubmusd10y?countrycode=bx")
    rate_str = tables[1]["Previous Close"][0]
    return float(rate_str.replace("%", "")) / 100
