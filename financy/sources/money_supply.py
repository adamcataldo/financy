import pandas as pd

url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=M2SL"


def monthly_money_supply():
    df = pd.read_csv(url)
    df.rename(columns={'DATE': 'date', 'M2SL': 'm2'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    df['m2'] = df['m2'] * 1.0e9
    return df