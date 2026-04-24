def early_breakout(df):

    try:
        if df is None or len(df) < 30:
            return False

        high = df["high"]
        close = df["close"]
        vol = df["volume"]

        resistance = high.tail(20).max()
        price = close.iloc[-1]

        vol_ma = vol.rolling(20).mean()

        # 🔥 breakout mạnh (confirm)
        breakout_strong = (
            price >= resistance * 0.95 and
            vol.iloc[-1] > vol_ma.iloc[-1] * 1.2
        )

        # 🔥 breakout sớm (tích lũy sát đỉnh)
        breakout_early = (
            price >= resistance * 0.90 and
            vol.iloc[-1] >= vol_ma.iloc[-1]
        )

        return breakout_strong or breakout_early

    except Exception as e:
        print("BREAKOUT ERROR:", e)
        return False
