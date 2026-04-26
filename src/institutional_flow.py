import pandas as pd
import numpy as np


# =========================
# EMA SMOOTH
# =========================
def ema_smooth(series, span=5):
    if len(series) < span:
        return series.iloc[-1]
    return series.ewm(span=span, adjust=False).mean().iloc[-1]


# =========================
# ACCUMULATION DAYS (SOFT)
# =========================
def accumulation_days(df):

    if len(df) < 20:
        return 0

    recent = df.tail(10)

    price_range = recent["high"].max() - recent["low"].min()
    avg_price = recent["close"].mean()

    if avg_price == 0:
        return 0

    vol = recent["volume"]
    vol_avg = df["volume"].rolling(20).mean().iloc[-1]

    if vol_avg == 0:
        return 0

    # sideway + volume support
    if price_range / avg_price < 0.06:
        score = (vol > vol_avg * 1.1).sum() / 10
        return score

    return 0.1  # 🔥 tránh dead zero


# =========================
# ABSORPTION SCORE (CONTINUOUS)
# =========================
def absorption_score(df):

    if len(df) < 5:
        return 0

    score = 0

    for i in range(-5, 0):
        vol = df["volume"].iloc[i]
        vol_avg = df["volume"].rolling(20).mean().iloc[i]
        close = df["close"].iloc[i]
        prev = df["close"].iloc[i - 1]

        if vol_avg == 0:
            continue

        if vol > vol_avg * 1.2:
            if close >= prev:
                score += 1
            else:
                score += 0.4  # 🔥 không drop về 0

    return score / 5


# =========================
# EXPANSION QUALITY (SMOOTH)
# =========================
def expansion_quality(df):

    if len(df) < 20:
        return 0

    high = df["high"].tail(20).max()
    close = df["close"].iloc[-1]

    vol = df["volume"]
    vol_avg = vol.rolling(20).mean().iloc[-1]

    if vol_avg == 0:
        return 0

    breakout_ratio = close / high

    # 🔥 continuous breakout strength
    break_score = np.tanh((breakout_ratio - 0.97) * 10)

    vol_ratio = vol.iloc[-1] / vol_avg
    vol_score = np.tanh((vol_ratio - 1) * 2)

    score = break_score * 1.5 + vol_score * 1.2

    return np.clip(score, -1, 1)


# =========================
# BUILD SERIES (REAL SMOOTH)
# =========================
def build_flow_series(df):

    series = []

    for i in range(25, len(df)):
        try:
            sub = df.iloc[:i]

            acc = accumulation_days(sub)
            absb = absorption_score(sub)
            exp = expansion_quality(sub)

            val = (
                acc * 1.0 +
                absb * 1.2 +
                exp * 1.5
            )

            series.append(val)

        except:
            continue

    if len(series) < 5:
        return None

    return pd.Series(series)


# =========================
# MAIN SCORE (V5 FINAL)
# =========================
def institutional_flow_score(df):

    try:
        if df is None or len(df) < 30:
            return 0

        series = build_flow_series(df)

        if series is None:
            return 0

        # =========================
        # 🔥 REAL EMA SMOOTH
        # =========================
        smooth = ema_smooth(series, span=5)

        # =========================
        # 🔥 NONLINEAR SCALE
        # =========================
        score = np.tanh(smooth * 1.5) * 2   # 🔥 scale [-1 → +2]

        return round(score, 3)

    except Exception as e:
        print("FLOW SCORE ERROR:", str(e))
        return 0
