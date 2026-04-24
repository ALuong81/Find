import pandas as pd
from data_loader import load_stock_data


def is_accumulating(df):

    try:
        if len(df) < 30:
            return False

        close = df["close"]
        volume = df["volume"]

        # giá đi ngang
        price_range = (close.max() - close.min()) / close.mean()

        # volume tăng dần
        vol_trend = volume.tail(10).mean() / volume.tail(20).mean()

        # spread nhỏ
        spread = (df["high"] - df["low"]) / close
        spread_avg = spread.tail(10).mean()

        if price_range < 0.08 and vol_trend > 1.2 and spread_avg < 0.03:
            return True

        return False

    except:
        return False


def accumulation_scan(df_symbols):

    results = []

    for _, row in df_symbols.iterrows():

        symbol = row["symbol"]

        try:
            df = load_stock_data(symbol)

            if is_accumulating(df):
                results.append(symbol)

        except:
            continue

    return results
