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
# 3. IMBALANCE (CONTINUOUS)
# =========================
def detect_imbalance(df):

    close = df["close"]
    open_ = df["open"]
    vol = df["volume"]

    up_vol = vol[close > open_].sum()
    down_vol = vol[close < open_].sum()

    if down_vol == 0:
        return 2.0  # cực mạnh

    ratio = up_vol / down_vol

    # 🔥 scale về ~[-1 → +2]
    score = np.tanh((ratio - 1) * 1.5) * 2

    return score


# =========================
# 4. ACCUMULATION ZONE (SOFT)
# =========================
def accumulation_score(df):

    hvn = detect_hvn(df)

    if hvn is None or hvn == 0:
        return 0

    price = df["close"].iloc[-1]

    dist = abs(price - hvn) / hvn

    # 🔥 càng gần HVN → score cao
    score = 1 - (dist / 0.05)

    return np.clip(score, -1, 1)


# =========================
# 5. EMA SMOOTH
# =========================
def ema_smooth(series, span=5):

    return series.ewm(span=span, adjust=False).mean().iloc[-1]


# =========================
# 6. MONEY FLOW SCORE (V4)
# =========================
def money_flow_score(df):

    try:
        if df is None or len(df) < 30:
            return 0

        # =========================
        # RAW COMPONENTS
        # =========================
        imbalance_raw = detect_imbalance(df)
        acc_raw = accumulation_score(df)

        # =========================
        # BUILD SERIES FOR SMOOTH
        # =========================
        imbalance_series = pd.Series(
            [detect_imbalance(df.iloc[:i]) for i in range(20, len(df))]
        )

        acc_series = pd.Series(
            [accumulation_score(df.iloc[:i]) for i in range(20, len(df))]
        )

        # =========================
        # EMA SMOOTH
        # =========================
        imbalance = ema_smooth(imbalance_series)
        acc = ema_smooth(acc_series)

        # =========================
        # FINAL SCORE
        # =========================
        score = (
            imbalance * 1.5 +
            acc * 1.2
        )

        # 🔥 normalize về [-1 → +2]
        score = np.tanh(score) * 2

        return score

    except Exception as e:
        print("FLOW ERROR:", str(e))
        return 0
    
