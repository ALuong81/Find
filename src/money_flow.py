import numpy as np

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

    max_idx = np.argmax(profile)

    hvn_price = levels[max_idx]

    return hvn_price


# =========================
# 3. IMBALANCE (CẦU > CUNG)
# =========================
def detect_imbalance(df):

    close = df["close"]
    open_ = df["open"]
    vol = df["volume"]

    up_vol = vol[close > open_].sum()
    down_vol = vol[close < open_].sum()

    if down_vol == 0:
        return 0

    return up_vol / down_vol


# =========================
# 4. ACCUMULATION ZONE
# =========================
def detect_accumulation_zone(df):

    hvn = detect_hvn(df)
    price = df["close"].iloc[-1]

    # giá gần HVN → tổ chức giữ vùng này
    if abs(price - hvn) / hvn < 0.03:
        return True

    return False


# =========================
# 5. MONEY FLOW SCORE
# =========================
def money_flow_score(df):

    score = 0

    imbalance = detect_imbalance(df)

    if imbalance > 1.2:
        score += 1

    if detect_accumulation_zone(df):
        score += 1

    return score
