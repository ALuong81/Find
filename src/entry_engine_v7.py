import numpy as np
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
# ENTRY SCORE ENGINE (V7.7 - REAL EDGE)
# =========================
def entry_score_v7(df):

    if len(df) < 60:
        return None

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # =========================
    # TREND (FIX: giữ nhưng không bóp)
    # =========================
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]

    trend_strength = abs(ma20 - ma50) / (ma50 + 1e-9)

    if trend_strength < 0.001:
        return None

    # =========================
    # RANGE
    # =========================
    recent_high = high.tail(20).max()
    recent_low = low.tail(20).min()
    range_pct = (recent_high - recent_low) / recent_low

    if range_pct > 0.25:
        return None

    # =========================
    # VOLATILITY
    # =========================
    vol_std_20 = close.pct_change().rolling(20).std().iloc[-1]
    vol_std_5 = close.pct_change().rolling(5).std().iloc[-1]

    vol_compress_score = max(0, (vol_std_20 - vol_std_5) * 20)

    # =========================
    # VOLUME (FIX: thêm expansion check)
    # =========================
    vol_mean = volume.rolling(20).mean().iloc[-1]
    vol_5 = volume.tail(5).mean()
    vol_ratio = volume.iloc[-1] / (vol_mean + 1e-9)
    vol_expand = volume.iloc[-1] / (vol_5 + 1e-9)

    # 🔥 nếu không có expansion thật → bỏ
    if vol_expand < 1.1:
        return None

    # =========================
    # RSI
    # =========================
    rsi = compute_rsi(close)
    if rsi > 95:
        return None

    # =========================
    # ATR
    # =========================
    atr = compute_atr(df)

    entry = close.iloc[-1]
    prev_close = close.iloc[-2]

    # =========================
    # BREAKOUT BUFFER
    # =========================
    recent_high_buffer = recent_high * 0.995

    #true_break = (prev_close < recent_high_buffer) and (entry >= recent_high_buffer)

    true_break = entry >= recent_high * 0.995
   
    # =========================
    # DISTANCE (ANTI CHASE)
    # =========================
    distance = (entry - recent_high) / (recent_high + 1e-9)

    if distance > 0.05:
        return None

    # =========================
    # 🔥 BREAKOUT QUALITY (NEW CORE EDGE)
    # =========================
    body = abs(close.iloc[-1] - df["open"].iloc[-1])
    candle_range = high.iloc[-1] - low.iloc[-1] + 1e-9
    body_ratio = body / candle_range

    if body_ratio < 0.5:   # 🔥 breakout yếu → loại
        return None

    # =========================
    # 🔥 MAIN BREAKOUT
    # =========================
    if true_break and vol_ratio >= 1.0:

        # 🔥 adaptive SL theo vol
        if vol_std_20 > 0.025:
            sl = entry - atr * 2.0
        else:
            sl = entry - atr * 1.6

        risk = entry - sl
        if risk <= 0:
            return None

        breakout_strength = max(0, distance)

        score = (
            (0.25 - range_pct) * 4 +
            vol_compress_score +
            vol_ratio * 2 +
            vol_expand * 2 +
            trend_strength * 8 +
            breakout_strength * 25 +
            body_ratio * 5
        )

        return {
            "entry": entry,
            "sl": sl,
            "score": score,
            "volatility": vol_std_20,
            "liquidity": vol_mean,
            "type": "breakout"
        }

    # =========================
    # 🔥 EARLY BREAK (TIGHTEN)
    # =========================
    if entry >= recent_high * 0.985:

        acc = detect_accumulation(df)

        distance_to_high = (recent_high - entry) / (recent_high + 1e-9)

        if vol_ratio >= 1.2 and acc and distance_to_high < 0.015:

            sl = entry - atr * 1.4
            risk = entry - sl

            if risk <= 0:
                return None

            score = (
                0.5 +
                vol_compress_score * 0.5 +
                vol_ratio * 1.3 +
                vol_expand * 1.5 +
                trend_strength * 6 +
                (1 - distance_to_high) * 4
            )

            return {
                "entry": entry,
                "sl": sl,
                "score": score,
                "volatility": vol_std_20,
                "liquidity": vol_mean,
                "type": "early_break"
            }

    return None
