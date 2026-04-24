import numpy as np

# =========================
# 1. ABSORPTION (HẤP THỤ)
# =========================
def detect_absorption(df):

    close = df["close"]
    low = df["low"]
    vol = df["volume"]

    # giá không giảm nhưng vol tăng
    down_move = close.diff() < 0
    vol_spike = vol > vol.rolling(20).mean()

    cond = (down_move & vol_spike).tail(5)

    # nếu nhiều phiên như vậy → có hấp thụ
    if cond.sum() >= 2:
        return True

    return False


# =========================
# 2. SHAKEOUT (RŨ HÀNG)
# =========================
def detect_shakeout(df):

    close = df["close"]
    low = df["low"]
    vol = df["volume"]

    prev_low = low.shift(1)

    # phá đáy giả
    fake_break = low < prev_low

    # nhưng đóng cửa lại cao
    recovery = close > low

    vol_spike = vol > vol.rolling(20).mean()

    cond = (fake_break & recovery & vol_spike).tail(3)

    if cond.sum() >= 1:
        return True

    return False


# =========================
# 3. TRAP (BẪY GIẢM)
# =========================
def detect_trap(df):

    close = df["close"]
    low = df["low"]

    support = low.tail(20).min()

    # phá support nhưng bật lại
    if close.iloc[-1] > support and low.iloc[-1] < support:
        return True

    return False


# =========================
# 4. INSTITUTION SCORE
# =========================
def institutional_score(df):

    score = 0

    if detect_absorption(df):
        score += 1

    if detect_shakeout(df):
        score += 1

    if detect_trap(df):
        score += 1

    return score
