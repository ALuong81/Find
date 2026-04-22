from vnstock import stock_historical_data
import datetime
from cache import load_cache, save_cache
from retry import retry

def load_stock_data(symbol):

    cached = load_cache(symbol)
    if cached is not None:
        return cached

    end = datetime.date.today()
    start = end - datetime.timedelta(days=200)

    df = retry(lambda: stock_historical_data(
        symbol=symbol,
        start_date=str(start),
        end_date=str(end),
        resolution="1D",
        type="stock"
    ))

    if df is None or df.empty:
        raise Exception(f"No data {symbol}")

    df.columns = [c.lower() for c in df.columns]

    save_cache(symbol, df)
    return df
