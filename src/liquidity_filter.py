import pandas as pd
from data_loader import load_stock_data

def calculate_liquidity(symbol):

    try:
        df = load_stock_data(symbol)

        vol = df["volume"].tail(20).mean()
        price = df["close"].iloc[-1]

        liquidity = vol * price

        return liquidity

    except:
        return 0


def rank_liquidity(df_symbols, top_n=50):

    results = []

    for _, row in df_symbols.iterrows():

        symbol = row["symbol"]

        liq = calculate_liquidity(symbol)

        results.append({
            "symbol": symbol,
            "liquidity": liq
        })

    df = pd.DataFrame(results)

    df = df.sort_values("liquidity", ascending=False)

    return df.head(top_n)
