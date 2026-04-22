import logging
logging.getLogger("vnstock").setLevel(logging.CRITICAL)

from vnstock import Vnstock
import datetime
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


def load_stock_data(symbol):

    if not is_valid_symbol(symbol):
        raise Exception(f"Invalid symbol {symbol}")

    cached = load_cache(symbol)
    if cached is not None:
        return cached

    end = datetime.date.today()
    start = end - datetime.timedelta(days=200)

    try:
        stock = Vnstock().stock(symbol=symbol, source="SSI")

        df = retry(lambda: stock.quote.history(
            start=str(start),
            end=str(end),
            interval="1D"
        ))

        if df is None or df.empty:
            raise Exception(f"No data {symbol}")

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

    except Exception as e:
        raise Exception(f"{symbol} load error: {str(e)}")


# ✅ INDEX PROXY (tránh lỗi VNINDEX)
def load_index():
    return load_stock_data("VCB")
