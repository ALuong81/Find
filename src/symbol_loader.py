import pandas as pd

def load_symbols():
    return pd.read_csv("data/full_symbols.csv")
