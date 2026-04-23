import pandas as pd
from data_loader import load_stock_data


# =========================
# MARKET CHECK
# =========================
def market_score():

    df = load_stock_data("VCB")  # proxy index

    ma20 = df["close"].rolling(20).mean().iloc[-1]
    price = df["close"].iloc[-1]

    if price > ma20:
        return 1
    return -1


# =========================
# STOCK SCORE
# =========================
def stock_score(df):

    # momentum
    momentum = (df["close"].iloc[-1] / df["close"].iloc[-20]) - 1

    # volume spike
    vol_now = df["volume"].iloc[-1]
    vol_avg = df["volume"].tail(20).mean()
    vol_score = vol_now / vol_avg if vol_avg else 0

    # trend
    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]
    trend = 1 if ma20 > ma50 else -1

    score = momentum * 2 + vol_score * 0.5 + trend

    return score


# =========================
# SECTOR FLOW
# =========================
def sector_money_flow(df_symbols):

    sector_map = {}

    for _, row in df_symbols.iterrows():

        symbol = row["symbol"]
        sector = row["sector"]

        try:
            df = load_stock_data(symbol)
            s = stock_score(df)

            if sector not in sector_map:
                sector_map[sector] = []

            sector_map[sector].append(s)

        except:
            continue

    results = []

    for sector, scores in sector_map.items():

        if len(scores) == 0:
            continue

        avg_score = sum(scores) / len(scores)

        results.append({
            "sector": sector,
            "score": avg_score
        })

    df = pd.DataFrame(results)

    return df.sort_values("score", ascending=False)


# =========================
# STOCK LEADER
# =========================
def pick_leaders(df_symbols, top_sector, top_n=3):

    stocks = df_symbols[df_symbols["sector"] == top_sector]

    results = []

    for _, row in stocks.iterrows():

        symbol = row["symbol"]

        try:
            df = load_stock_data(symbol)
            s = stock_score(df)

            results.append({
                "symbol": symbol,
                "score": s
            })

        except:
            continue

    df = pd.DataFrame(results)

    return df.sort_values("score", ascending=False).head(top_n)
