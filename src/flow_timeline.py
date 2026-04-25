def flow_timeline(df):

    try:
        vol = df["volume"]
        close = df["close"]

        vol_ma5 = vol.rolling(5).mean()
        vol_ma20 = vol.rolling(20).mean()

        price_change = close.pct_change()

        recent_flow = (price_change * vol).tail(5).mean()
        base_flow = (price_change * vol).tail(20).mean()

        if base_flow == 0:
            return 0

        acceleration = recent_flow / abs(base_flow)

        return max(0, min(acceleration, 2))

    except:
        return 0
