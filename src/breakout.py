def early_breakout(df):

    if len(df) < 30:
        return False

    high = df["high"]
    close = df["close"]
    vol = df["volume"]

    # 🔥 kháng cự
    resistance = high.tail(20).max()

    # 🔥 volume tăng
    vol_ma = vol.rolling(20).mean()
    vol_spike = vol.iloc[-1] > vol_ma.iloc[-1] * 1.1

    # 🔥 giá tiến sát kháng cự
    price = close.iloc[-1]
    near_break = price >= resistance * 0.93

    return near_break and vol_spike
