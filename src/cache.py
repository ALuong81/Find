import os
import pandas as pd
import time

CACHE_DIR = "data/cache"

def load_cache(symbol):

    path = f"{CACHE_DIR}/{symbol}.csv"

    if not os.path.exists(path):
        return None

    # 🔥 nếu cache < 1 ngày → dùng luôn
    if time.time() - os.path.getmtime(path) < 86400:
        return pd.read_csv(path)

    return None
