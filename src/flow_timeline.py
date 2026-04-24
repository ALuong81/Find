def flow_timeline(df):

    try:
        if df is None or len(df) < 30:
            return 0

        close = df["close"]
        volume = df["volume"]

        # money flow = price change * volume
        flow = (close.pct_change() * volume).fillna(0)

        # xu hướng 5 ngày
        recent = flow.tail(5).sum()

        # xu hướng 10 ngày
        base = flow.tail(10).sum()

        if base == 0:
            return 0

        # 🔥 acceleration
        score = recent / abs(base)

        return score

    except:
        return 0
