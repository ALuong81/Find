from fibo import fibo

def validate_entry(df):

    f = fibo(df)
    p = df["close"].iloc[-1]

    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]

    # trend filter
    if ma20 < ma50:
        return False, f

    high_20 = df["high"].rolling(20).max().iloc[-2]

    # 🔥 CASE 1: pullback
    if abs(p - f["entry"]) / p < 0.04:
        return True, f

    # 🔥 CASE 2: breakout
    if p > high_20:
        f["entry"] = p
        f["sl"] = p * 0.95
        f["tp1"] = p * 1.05
        f["tp2"] = p * 1.1
        return True, f

    return False, f