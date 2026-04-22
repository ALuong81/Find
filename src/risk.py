def market_risk(df):

    ma = df["close"].rolling(50).mean().iloc[-1]
    p = df["close"].iloc[-1]

    return 3 if p < ma else 1
