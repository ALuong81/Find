import numpy as np
from breakout import breakout_type
from accumulation import detect_accumulation

# =========================
# UTIL
# =========================
def compute_atr(df, period=14):
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr = np.maximum(
        high - low,
        np.maximum(
            abs(high - close.shift()),
            abs(low - close.shift())
        )
    )
    atr = tr.rolling(period).mean().iloc[-1]

    if np.isnan(atr) or atr <= 0:
        atr = (high - low).rolling(20).mean().iloc[-1]
        if np.isnan(atr) or atr <= 0:
            atr = close.iloc[-1] * 0.02

    return float(atr)


def compute_rsi(close, period=14):
    delta = close.diff()
    up = np.maximum(delta, 0.0)
    down = np.maximum(-delta, 0.0)

    ma_up = up.rolling(period).mean()
    ma_down = down.rolling(period).mean()

    rs = ma_up / (ma_down + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])


# =========================
# ENTRY SCORE ENGINE (V7)
# =========================
def entry_score_v7(df):

    if len(df) < 60:
        return None

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # =========================
    # 1. RANGE (NỚI RA)
    # =========================
    recent_high = high.tail(20).max()
    recent_low = low.tail(20).min()

    range_pct = (recent_high - recent_low) / recent_low

    if range_pct > 0.18:   # 🔥 từ 0.12 → 0.18
        return None

    # =========================
    # 2. VOL COMPRESSION (NỚI)
    # =========================
    vol_std_20 = close.pct_change().rolling(20).std().iloc[-1]
    vol_std_5 = close.pct_change().rolling(5).std().iloc[-1]

    if vol_std_5 > vol_std_20 * 1.2:   # 🔥 cho phép lệch nhẹ
        return None

    # =========================
    # 3. BREAKOUT (NỚI)
    # =========================
    entry = close.iloc[-1]

    if entry < recent_high * 0.995:   # 🔥 từ 1.01 → 0.995
        return None

    # =========================
    # 4. VOLUME (NỚI)
    # =========================
    vol_mean = volume.rolling(20).mean().iloc[-1]

    if volume.iloc[-1] < vol_mean * 1.2:   # 🔥 từ 1.5 → 1.2
        return None

    # =========================
    # 5. SL
    # =========================
    sl = recent_low
    risk = entry - sl

    if risk <= 0:
        return None

    # =========================
    # 6. SCORE
    # =========================
    score = 0
    score += (0.18 - range_pct) * 8
    score += (vol_std_20 - vol_std_5) * 30
    score += (volume.iloc[-1] / vol_mean)

    return {
        "entry": entry,
        "sl": sl,
        "score": score,
        "volatility": vol_std_20,
        "liquidity": vol_mean,
        "type": "breakout"
    }
