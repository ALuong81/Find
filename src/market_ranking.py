from parallel import parallel_map
from relative_strength import relative_strength
from data_loader import load_index


def process(row, load_stock_data, df_index):

    symbol = row["symbol"]
    sector = row["sector"]

    try:
        df = load_stock_data(symbol)

        ret = df["close"].pct_change(20).iloc[-1]
        vol = df["volume"].iloc[-1] / df["volume"].rolling(20).mean().iloc[-1]
        rs = relative_strength(df, df_index)

        score = ret * 0.4 + rs * 0.4 + vol * 0.2

        return {
            "symbol": symbol,
            "sector": sector,
            "score": score
        }

    except:
        return None


def market_ranking(df_symbols, load_stock_data):

    # ✅ dùng index proxy thay vì VNINDEX
    df_index = load_index()

    rows = df_symbols.to_dict("records")

    results = parallel_map(
        lambda r: process(r, load_stock_data, df_index),
        rows,
        max_workers=10
    )

    # lọc None
    results = [r for r in results if r is not None]

    return sorted(results, key=lambda x: x["score"], reverse=True)
