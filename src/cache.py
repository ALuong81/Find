import os
import pandas as pd

CACHE_DIR = "data/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def path(symbol):
    return f"{CACHE_DIR}/{symbol}.csv"

def load_cache(symbol):
    if os.path.exists(path(symbol)):
        return pd.read_csv(path(symbol))
    return None

def save_cache(symbol, df):
    df.to_csv(path(symbol), index=False)
