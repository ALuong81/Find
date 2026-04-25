def detect_market_regime(df_index):

    close = df_index["close"]

    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]

    vol = df_index["volume"].tail(20).mean()
    vol_now = df_index["volume"].iloc[-1]

    trend = "UP" if ma20 > ma50 else "DOWN"
    volatility = vol_now / vol if vol > 0 else 1

    if trend == "UP" and volatility > 1.2:
        return "TREND_STRONG"

    if trend == "UP":
        return "TREND_WEAK"

    if trend == "DOWN" and volatility > 1.2:
        return "DISTRIBUTION"

    return "SIDEWAY"
