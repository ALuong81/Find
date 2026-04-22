from parallel import parallel_map
from relative_strength import relative_strength

def process(row, load_stock_data, df_index):

    df = load_stock_data(row["symbol"])

    ret = df["close"].pct_change(20).iloc[-1]
    vol = df["volume"].iloc[-1] / df["volume"].rolling(20).mean().iloc[-1]
    rs = relative_strength(df, df_index)

    score = ret*0.4 + rs*0.4 + vol*0.2

    return {
        "symbol": row["symbol"],
        "sector": row["sector"],
        "score": score
    }

def market_ranking(df_symbols, load_stock_data):

    df_index = load_stock_data("VNINDEX")

    rows = df_symbols.to_dict("records")

    res = parallel_map(lambda r: process(r, load_stock_data, df_index), rows)

    return sorted(res, key=lambda x: x["score"], reverse=True)
