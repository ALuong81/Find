from data_loader import load_index

def market_ranking(df_symbols, load_stock_data):

    df_index = load_index()

    results = []

    for _, row in df_symbols.iterrows():
        try:
            df = load_stock_data(row["symbol"])

            ret = df["close"].pct_change(20).iloc[-1]
            vol = df["volume"].iloc[-1] / df["volume"].rolling(20).mean().iloc[-1]

            score = ret*0.6 + vol*0.4

            results.append({
                "symbol": row["symbol"],
                "sector": row["sector"],
                "score": score
            })
        except:
            continue

    return sorted(results, key=lambda x: x["score"], reverse=True)
