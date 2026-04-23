from fibo import fibo
from timeframe import resample_h1

def validate_entry(df):

    f = fibo(df)

    h1 = resample_h1(df)
    p = h1["close"].iloc[-1]

    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]

    if ma20 < ma50:
        return False, f

    high20 = df["high"].rolling(20).max().iloc[-2]

    # pullback
    if abs(p - f["entry"]) / p < 0.04:
        return True, f

    # breakout
    if p > high20:
        f["entry"] = p
        f["sl"] = p * 0.95
        f["tp1"] = p * 1.05
        f["tp2"] = p * 1.1
        return True, f

    return False, f
