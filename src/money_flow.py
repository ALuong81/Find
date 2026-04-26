import numpy as np
import pandas as pd


# =========================
# 1. VOLUME BY PRICE (VBP)
# =========================
def volume_profile(df, bins=20):

    close = df["close"]
    vol = df["volume"]

    price_min = close.min()
    price_max = close.max()

    levels = np.linspace(price_min, price_max, bins)
    profile = np.zeros(len(levels))

    for i in range(len(close)):
        idx = np.searchsorted(levels, close.iloc[i]) - 1
        if 0 <= idx < len(profile):
            profile[idx] += vol.iloc[i]

    return levels, profile


# =========================
# 2. HIGH VOLUME NODE (HVN)
# =========================
def detect_hvn(df):

    levels, profile = volume_profile(df)

    if len(profile) == 0:
        return None

    max_idx = np.argmax(profile)
    return levels[max_idx]


# =========================
# 3. IMBALANCE (IMPROVED)
# =========================
def detect_imbalance(df):

    close = df["close"]
    open_ = df["open"]
    vol = df["volume"]

    up_vol = vol[close > open_].sum()
    down_vol = vol[close < open_].sum()

    total = up_vol + down_vol

    if total == 0:
        return 0

    # 🔥 normalize ratio → tránh explode
    imbalance = (up_vol - down_vol) / total

    # 🔥 scale mượt hơn (không bị spike)
    score = np.tanh(imbalance * 3)

    return score


# =========================
# 4. ACCUMULATION (SOFT + STABLE)
# =========================
def accumulation_score(df):

    hvn = detect_hvn(df)

    if hvn is None or hvn == 0:
        return 0

    price = df["close"].iloc[-1]

    dist = abs(price - hvn) / hvn

    # 🔥 vùng tốt: <3%
    if dist < 0.03:
        score = 1 - (dist / 0.03)
    else:
        score = - (dist - 0.03) * 5  # penalize nhẹ

    return np.clip(score, -1, 1)


# =========================
# 5. EMA SMOOTH (FAST)
# =========================
def ema_smooth(series, span=3):  # 🔥 giảm lag
    return series.ewm(span=span, adjust=False).mean().iloc[-1]


# =========================
# 6. MONEY FLOW SCORE V4 FINAL
# =========================
def money_flow_score(df):

    try:
        if df is None or len(df) < 30:
            return 0

        # =========================
        # BUILD SERIES (LIGHTWEIGHT)
        # =========================
        imbalance_series = []
        acc_series = []

        for i in range(25, len(df)):
            sub = df.iloc[:i]

            imbalance_series.append(detect_imbalance(sub))
            acc_series.append(accumulation_score(sub))

        if len(imbalance_series) < 5:
            return 0

        imbalance_series = pd.Series(imbalance_series)
        acc_series = pd.Series(acc_series)

        # =========================
        # 🔥 FAST SMOOTH
        # =========================
        imbalance = ema_smooth(imbalance_series, span=3)
        acc = ema_smooth(acc_series, span=3)

        # =========================
        # 🔥 FINAL SCORE (REBALANCED)
        # =========================
        score = (
            imbalance * 1.3 +
            acc * 1.1
        )

        # 🔥 expand range (tránh bị bóp nhỏ)
        score = np.tanh(score * 1.5) * 2

        return score

    except Exception as e:
        print("FLOW ERROR:", str(e))
        return 0
