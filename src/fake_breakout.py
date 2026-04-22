def detect_fake_breakout(df):

    breakout = df["close"].iloc[-2] > df["high"].rolling(20).max().iloc[-3]
    fail = df["close"].iloc[-1] < df["close"].iloc[-2]

    return breakout and fail
