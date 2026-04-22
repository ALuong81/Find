from vnstock import Vnstock
import datetime
from cache import load_cache, save_cache
from retry import retry

def load_index():

    from vnstock import Vnstock
    import datetime

    end = datetime.date.today()
    start = end - datetime.timedelta(days=200)

    stock = Vnstock().stock(symbol="VCB", source="VCI")  
    # hack: dùng 1 mã để lấy API object

    df = stock.quote.history(
        start=str(start),
        end=str(end),
        interval="1D"
    )

    # ⚠️ giả lập index = trung bình (fallback)
    df["close"] = df["close"].rolling(5).mean()

    return df
    
def load_stock_data(symbol):

    cached = load_cache(symbol)
    if cached is not None:
        return cached

    end = datetime.date.today()
    start = end - datetime.timedelta(days=200)

    try:
        stock = Vnstock().stock(symbol=symbol, source="VCI")

        df = retry(lambda: stock.quote.history(
            start=str(start),
            end=str(end),
            interval="1D"
        ))

        if df is None or df.empty:
            raise Exception(f"No data {symbol}")

        # chuẩn hóa tên cột
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
