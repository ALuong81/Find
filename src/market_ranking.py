from data_loader import load_index
from relative_strength import relative_strength


def market_ranking(df_symbols, load_stock_data):

    df_index = load_index()

    results = []

    for _, row in df_symbols.iterrows():

        try:
            df = load_stock_data(row["symbol"])

            ret = df["close"].pct_change(20).iloc[-1]
            vol = df["volume"].iloc[-1] / df["volume"].rolling(20).mean().iloc[-1]
            rs = relative_strength(df, df_index)

            score = ret*0.4 + rs*0.4 + vol*0.2

            results.append({
                "symbol": row["symbol"],
                "sector": row["sector"],
                "score": score
            })

        except:
            continue

    return sorted(results, key=lambda x: x["score"], reverse=True)
