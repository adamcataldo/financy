import pandas as pd

# From Wikipedia page
def sp_500_constituents():
    x = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    return x[0].Symbol

def nasdaq_100_constituents():
    x = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100#Components")
    return x[3].Ticker

def etf_constituents(etf):
    fns = {'SPX' : sp_500_constituents,
           'NDX' : nasdaq_100_constituents}
    return fns[etf]()
