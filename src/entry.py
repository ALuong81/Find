def fibo(df):

    h = df["high"].rolling(20).max().iloc[-1]
    l = df["low"].rolling(20).min().iloc[-1]

    d = h - l

    return {
        "entry": h - 0.382*d,
        "sl": l,
        "tp1": h + 0.618*d,
        "tp2": h + d
    }

def validate_entry(df):

    f = fibo(df)
    p = df["close"].iloc[-1]

    if abs(p - f["entry"]) / p < 0.03:
        return True, f

    return False, f
