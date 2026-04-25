import logging
logging.getLogger("vnstock").setLevel(logging.CRITICAL)

from vnstock import Vnstock
import datetime, time, random, os
import pandas as pd

from cache import load_cache, save_cache
from retry import retry

memory_cache = {}
MARKET_DIR = "data/market"

def is_valid_symbol(symbol):
    symbol = str(symbol).upper()
    return not (
        symbol is None or
        "VNINDEX" in symbol or
        symbol.startswith(("E1","FU","CW","C")) or
        len(symbol) > 4
    )

def fetch_with_source(symbol, source, start, end):
    try:
        time.sleep(random.uniform(0.4,0.8))
        stock = Vnstock().stock(symbol=symbol, source=source)
        df = stock.quote.history(start=str(start), end=str(end), interval="1D")
        if df is not None and not df.empty:
            return df
    except:
        return None
    return None

def load_stock_data(symbol):

    if not is_valid_symbol(symbol):
        raise Exception(f"Invalid symbol {symbol}")

    if symbol in memory_cache:
        return memory_cache[symbol]

    # 🔥 LOCAL DATA
    path = f"{MARKET_DIR}/{symbol}.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        memory_cache[symbol] = df
        print(f"LOAD LOCAL: {symbol}")
        return df

    # fallback cache
    cached = load_cache(symbol)
    if cached is not None:
        memory_cache[symbol] = cached
        return cached

    end = datetime.date.today()
    start = end - datetime.timedelta(days=200)

    for src in ["VCI","MSN","KBS"]:
        df = retry(lambda: fetch_with_source(symbol, src, start, end))
        if df is not None:
            break

    if df is None:
        raise Exception(f"{symbol} no data")

    df = df.rename(columns={
        "time":"date","open":"open","high":"high",
        "low":"low","close":"close","volume":"volume"
    })

    save_cache(symbol, df)
    memory_cache[symbol] = df

    return df

def load_stock_data_h1(symbol):

    try:
        from vnstock import stock_historical_data

        df = stock_historical_data(
            symbol=symbol,
            resolution="60",   # 🔥 H1
            start_date="2024-01-01",
            end_date=None
        )

        return df

    except:
        return None
        
def load_index():
    for s in ["VCB","BID","CTG"]:
        try:
            return load_stock_data(s)
        except:
            continue
    raise Exception("No index")
