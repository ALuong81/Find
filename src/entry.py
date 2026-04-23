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

    # 🔥 entry chính xác hơn
    if abs(p - f["entry"]) / p < 0.03:
        return True, f

    return False, f
