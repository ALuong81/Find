import os
import pandas as pd
import time

CACHE_DIR = "data/cache"

os.makedirs(CACHE_DIR, exist_ok=True)


def path(symbol):
    return f"{CACHE_DIR}/{symbol}.csv"


def load_cache(symbol):

    p = path(symbol)

    if not os.path.exists(p):
        return None

    # 🔥 cache < 1 ngày thì dùng
    if time.time() - os.path.getmtime(p) < 86400:
        try:
            return pd.read_csv(p)
        except:
            return None

    return None


def save_cache(symbol, df):

    p = path(symbol)

    try:
        df.to_csv(p, index=False)
    except:
        pass
