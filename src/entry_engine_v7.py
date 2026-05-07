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
# ENTRY SCORE ENGINE (V7.8 - CLEAN EDGE)
# =========================
def entry_score_v7(df):

    if len(df) < 60:
        return None

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # =========================
    # TREND (FIX: siết lại)
    # =========================
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]

    if ma20 < ma50:
        return None  # 🔥 thêm lại trend filter

    trend_strength = abs(ma20 - ma50) / (ma50 + 1e-9)
    if trend_strength < 0.003:   # 🔥 tăng từ 0.001 → 0.003
        return None

    # =========================
    # RANGE (siết)
    # =========================
    recent_high = high.tail(20).max()
    recent_low = low.tail(20).min()
    range_pct = (recent_high - recent_low) / recent_low

    if range_pct > 0.22:   # 🔥 giảm từ 0.25 → 0.22
        return None

    # =========================
    # VOLATILITY
    # =========================
    vol_std_20 = close.pct_change().rolling(20).std().iloc[-1]
    vol_std_5 = close.pct_change().rolling(5).std().iloc[-1]

    vol_compress_score = max(0, (vol_std_20 - vol_std_5) * 20)

    # =========================
    # VOLUME (siết mạnh)
    # =========================
    vol_mean = volume.rolling(20).mean().iloc[-1]
    vol_5 = volume.tail(5).mean()

    vol_ratio = volume.iloc[-1] / (vol_mean + 1e-9)
    vol_expand = volume.iloc[-1] / (vol_5 + 1e-9)

    if vol_expand < 1.2:   # 🔥 tăng từ 1.1 → 1.2
        return None

    # =========================
    # RSI (siết lại)
    # =========================
    rsi = compute_rsi(close)
    if rsi > 90:   # 🔥 giảm từ 95 → 85
        return None

    # =========================
    # ATR
    # =========================
    atr = compute_atr(df)

    entry = close.iloc[-1]

    # =========================
    # 🔥 TRUE BREAK (FIX QUAN TRỌNG NHẤT)
    # =========================
    prev_close = close.iloc[-2]

    true_break = (
        (prev_close < recent_high * 0.995) and
        (entry > recent_high * 1.003)
    )

    distance = (entry - recent_high) / (recent_high + 1e-9)

    if distance > 0.03:   # 🔥 giảm từ 0.05 → 0.02
        return None

    # =========================
    # CANDLE QUALITY (siết)
    # =========================
    body = abs(close.iloc[-1] - df["open"].iloc[-1])
    candle_range = high.iloc[-1] - low.iloc[-1] + 1e-9
    body_ratio = body / candle_range

    if body_ratio < 0.6:   # 🔥 tăng từ 0.5 → 0.6
        return None

    # =========================
    # 🔥 MAIN BREAKOUT (UPGRADE)
    # =========================
    if true_break and vol_ratio >= 1.2:   # 🔥 tăng từ 1.0 → 1.5

        if vol_std_20 > 0.025:
            sl = entry - atr * 2.2
        else:
            sl = entry - atr * 1.8

        risk = entry - sl
        if risk <= 0:
            return None

        breakout_strength = distance

        score = (
            (0.22 - range_pct) * 4 +
            vol_compress_score * 0.8 +
            vol_ratio * 3 +
            vol_expand * 2 +
            trend_strength * 12 +
            breakout_strength * 50 +
            body_ratio * 6
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
    # 🔥 EARLY BREAK (SIẾT)
    # =========================
    if entry >= recent_high * 0.99:

        acc = detect_accumulation(df)

        distance_to_high = (recent_high - entry) / (recent_high + 1e-9)

        if vol_ratio >= 1.5 and acc and distance_to_high < 0.008:

            sl = entry - atr * 1.6
            risk = entry - sl

            if risk <= 0:
                return None

            score = (
                0.5 +
                vol_compress_score * 0.5 +
                vol_ratio * 1.5 +
                vol_expand * 1.5 +
                trend_strength * 8 +
                (1 - distance_to_high) * 5
            )

            return {
                "entry": entry,
                "sl": sl,
                "score": score,
                "volatility": vol_std_20,
                "liquidity": vol_mean,
                "type": "early_break"
            }

    # ❌ 🔥 XÓA HOÀN TOÀN WEAK BREAK
    # → không return gì nữa

    return None
