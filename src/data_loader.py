import logging
logging.getLogger("vnstock").setLevel(logging.CRITICAL)

from vnstock import Vnstock
import datetime, time, random, os
import pandas as pd

from cache import load_cache, save_cache
from retry import retry

# =========================
# 🔥 CONFIG
# =========================

memory_cache = {}

# 🔥 AUTO detect data branch (GitHub Actions)
if os.path.exists("data-branch/data/market"):
    MARKET_DIR = "data-branch/data/market"
else:
    MARKET_DIR = "data/market"


# =========================
# 🔥 VALID SYMBOL
# =========================
def is_valid_symbol(symbol):
    symbol = str(symbol).upper()
    return not (
        symbol is None or
        "VNINDEX" in symbol or
        symbol.startswith(("E1", "FU", "CW", "C")) or
        len(symbol) > 4
    )


# =========================
# 🔥 FETCH DATA
# =========================
def fetch_with_source(symbol, source, start, end):
    try:
        time.sleep(random.uniform(0.4, 0.8))
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


# =========================
# 🔥 NORMALIZE DATA
# =========================
def normalize_df(df):

    df = df.rename(columns={
        "time": "date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume"
    })

    # 🔥 FIX DATETIME (QUAN TRỌNG cho backtest)
    df["date"] = pd.to_datetime(df["date"])

    df = df.sort_values("date")
    df = df.drop_duplicates(subset=["date"])

    return df


# =========================
# 🔥 LOAD STOCK DATA (D1)
# =========================
def load_stock_data(symbol):

    if not is_valid_symbol(symbol):
        raise Exception(f"Invalid symbol {symbol}")

    if symbol in memory_cache:
        return memory_cache[symbol]

    path = f"{MARKET_DIR}/{symbol}.csv"

    # =========================
    # 🔥 LOAD LOCAL
    # =========================
    if os.path.exists(path):

        df = pd.read_csv(path)

        if "date" not in df.columns:
            raise Exception(f"{symbol} corrupted data")

        df["date"] = pd.to_datetime(df["date"])

        memory_cache[symbol] = df

        print(f"LOAD LOCAL: {symbol}")
        return df

    # =========================
    # 🔥 CACHE
    # =========================
    cached = load_cache(symbol)
    if cached is not None:
        cached["date"] = pd.to_datetime(cached["date"])
        memory_cache[symbol] = cached
        return cached

    # =========================
    # 🔥 FETCH ONLINE
    # =========================
    end = datetime.date.today()
    start = end - datetime.timedelta(days=200)

    df = None

    for src in ["VCI", "MSN", "KBS"]:
        df = retry(lambda: fetch_with_source(symbol, src, start, end))
        if df is not None:
            break

    if df is None:
        raise Exception(f"{symbol} no data")

    df = normalize_df(df)

    save_cache(symbol, df)
    memory_cache[symbol] = df

    return df


# =========================
# 🔥 LOAD H1 DATA
# =========================
def load_stock_data_h1(symbol):

    try:
        from vnstock import stock_historical_data

        df = stock_historical_data(
            symbol=symbol,
            resolution="60",
            start_date="2024-01-01",
            end_date=None
        )

        if df is None or df.empty:
            return None

        df["time"] = pd.to_datetime(df["time"])

        return df

    except:
        return None


# =========================
# 🔥 LOAD INDEX (proxy)
# =========================
def load_index():

    # 🔥 dùng bank làm proxy thị trường
    for s in ["VCB", "BID", "CTG"]:
        try:
            return load_stock_data(s)
        except:
            continue

    raise Exception("No index")
