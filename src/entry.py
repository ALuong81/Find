from fibo import fibo
from timeframe import resample_h1

def validate_entry(df):

    f = fibo(df)

    h1 = resample_h1(df)
    p = h1["close"].iloc[-1]

    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]

    vol = df["volume"].iloc[-1]
    vol_avg = df["volume"].rolling(20).mean().iloc[-1]

    high20 = df["high"].rolling(20).max().iloc[-2]

    # 🔥 1. xu hướng
    if ma20 < ma50:
        return False, f

    # 🔥 2. breakout sớm (nới điều kiện)
    if p > high20 * 0.98:
        f["entry"] = p
        f["sl"] = p * 0.95
        f["tp1"] = p * 1.05
        f["tp2"] = p * 1.1
        return True, f

    # 🔥 3. pullback linh hoạt hơn
    if abs(p - f["entry"]) / p < 0.07:
        return True, f

    # 🔥 4. volume xác nhận
    if vol > vol_avg * 1.3:
        f["entry"] = p
        f["sl"] = p * 0.94
        f["tp1"] = p * 1.06
        f["tp2"] = p * 1.12
        return True, f

    return False, f
