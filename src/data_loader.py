import logging
logging.getLogger("vnstock").setLevel(logging.CRITICAL)

from vnstock import Vnstock
import datetime
import time
import random

from cache import load_cache, save_cache
from retry import retry

def is_valid_symbol(symbol):

    if symbol is None:
        return False

    symbol = str(symbol).upper()

    if "VNINDEX" in symbol:
        return False
    if symbol.startswith(("E1", "FU", "CW", "C")):
        return False
    if len(symbol) > 4:
        return False

    return True


def fetch_with_source(symbol, source, start, end):

    try:
        time.sleep(random.uniform(0.3, 0.7))

        stock = Vnstock().stock(symbol=symbol, source=source)

        df = stock.quote.history(
            start=str(start),
            end=str(end),
            interval="1D"
        )

        if df is not None and not df.empty:
            return df

    except:
        return None

    return None


def load_stock_data(symbol):

    if not is_valid_symbol(symbol):
        raise Exception(f"Invalid symbol {symbol}")

    cached = load_cache(symbol)
    if cached is not None:
        return cached

    end = datetime.date.today()
    start = end - datetime.timedelta(days=200)

    sources = ["VCI", "MSN", "KBS"]

    df = None

    for src in sources:
        #df = fetch_with_source(symbol, src, start, end)
        df = retry(lambda: fetch_with_source(symbol, src, start, end)) 
        if df is not None:
            break

    if df is None or df.empty:
        raise Exception(f"{symbol} no data")

    df = df.rename(columns={
        "time": "date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume"
    })

    save_cache(symbol, df)

    return df


def load_index():

    for sym in ["VCB", "BID", "CTG"]:
        try:
            return load_stock_data(sym)
        except:
            continue

    raise Exception("Cannot load index proxy")
