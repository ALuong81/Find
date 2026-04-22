def add_indicators(df):

    df["ma20"] = df["close"].rolling(20).mean()
    df["ma50"] = df["close"].rolling(50).mean()

    df["vol_avg"] = df["volume"].rolling(20).mean()

    return df
