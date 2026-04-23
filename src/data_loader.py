import logging
logging.getLogger("vnstock").setLevel(logging.CRITICAL)

from vnstock import Vnstock
import datetime
import time
import random

from cache import load_cache, save_cache
from retry import retry

# 🔥 cache RAM (tránh gọi lại trong cùng 1 run)
memory_cache = {}


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
        # 🔥 delay tránh rate limit
        time.sleep(random.uniform(0.4, 0.8))

        stock = Vnstock().stock(symbol=symbol, source=source)

        df = stock.quote.history(
            start=str(start),
            end=str(end),
            interval="1D"
        )

        if df is not None and not df.empty:
            return df

    except Exception as e:
        return None

    return None


def load_stock_data(symbol):

    if not is_valid_symbol(symbol):
        raise Exception(f"Invalid symbol {symbol}")

    # 🔥 1. cache RAM (nhanh nhất)
    if symbol in memory_cache:
        return memory_cache[symbol]

    # 🔥 2. cache file
    cached = load_cache(symbol)
    if cached is not None:
        memory_cache[symbol] = cached
        return cached

    # 🔥 3. gọi API
    end = datetime.date.today()
    start = end - datetime.timedelta(days=200)

    sources = ["VCI", "MSN", "KBS"]

    df = None

    for src in sources:

        df = retry(lambda: fetch_with_source(symbol, src, start, end))

        if df is not None:
            break

    if df is None or df.empty:
        raise Exception(f"{symbol} no data")

    # chuẩn hóa cột
    df = df.rename(columns={
        "time": "date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume"
    })

    # 🔥 lưu cache
    save_cache(symbol, df)

    # 🔥 lưu RAM
    memory_cache[symbol] = df

    return df


def load_index():

    # dùng cổ bank làm proxy thị trường
    for sym in ["VCB", "BID", "CTG"]:
        try:
            return load_stock_data(sym)
        except:
            continue

    raise Exception("Cannot load index proxy")
