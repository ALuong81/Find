import pandas as pd
from data_loader import load_stock_data
from institutional import institutional_score
from money_flow import money_flow_score


def compute_stock_score(df):

    try:
        close = df["close"]
        volume = df["volume"]

        price_change = close.iloc[-1] / close.iloc[-5] - 1
        vol = volume.iloc[-5:].mean()

        mf = money_flow_score(df)
        inst = institutional_score(df)

        score = price_change * vol * (1 + mf + inst)

        return score

    except:
        return 0


def market_heatmap(df_symbols):

    data = []

    for _, row in df_symbols.iterrows():

        symbol = row["symbol"]
        sector = row["sector"]

        try:
            df = load_stock_data(symbol)

            score = compute_stock_score(df)

            data.append({
                "symbol": symbol,
                "sector": sector,
                "score": score
            })

        except:
            continue

    df = pd.DataFrame(data)

    if df.empty:
        return None

    # 🔥 gom theo sector
    heatmap = (
        df.groupby("sector")["score"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    return heatmap
