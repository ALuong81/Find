from fibo import fibo

def validate_entry(df):

    f = fibo(df)
    p = df["close"].iloc[-1]

    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]

    # chỉ trade uptrend
    if ma20 < ma50:
        return False, f

    # gần vùng entry
    if abs(p - f["entry"]) / p < 0.025:
        return True, f

    return False, f
