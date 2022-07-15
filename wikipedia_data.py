import pandas as pd

# From Wikipedia page
def sp_500_constituents():
    x = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    return x[0].Symbol