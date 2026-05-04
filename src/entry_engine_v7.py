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
# ENTRY SCORE ENGINE (V7.3 - EDGE FIX)
# =========================
def entry_score_v7(df):

    if len(df) < 60:
        return None

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    recent_high = high.tail(20).max()
    recent_low = low.tail(20).min()
    range_pct = (recent_high - recent_low) / recent_low

    if range_pct > 0.22:
        return None

    # =========================
    # VOL
    # =========================
    vol_std_20 = close.pct_change().rolling(20).std().iloc[-1]
    vol_std_5 = close.pct_change().rolling(5).std().iloc[-1]
    vol_compress_score = max(0, (vol_std_20 - vol_std_5) * 20)

    # =========================
    # VOLUME
    # =========================
    vol_mean = volume.rolling(20).mean().iloc[-1]
    vol_ratio = volume.iloc[-1] / (vol_mean + 1e-9)

    # =========================
    # RSI
    # =========================
    rsi = compute_rsi(close)
    if rsi > 78:
        return None

    # =========================
    # ATR (🔥 QUAN TRỌNG)
    # =========================
    atr = compute_atr(df)

    entry = close.iloc[-1]

    # =========================
    # 🔥 MAIN BREAKOUT
    # =========================
    if entry >= recent_high * 0.995 and vol_ratio >= 1.3:

        # ❗ SL mới (ATR-based)
        sl = entry - atr * 1.5
        risk = entry - sl

        if risk <= 0:
            return None

        score = (
            (0.22 - range_pct) * 6 +
            vol_compress_score +
            vol_ratio * 2 +          # 🔥 tăng weight volume
            (1 - abs(entry - recent_high)/recent_high) * 5
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
    # 🔥 EARLY BREAK (ANTI FAKE)
    # =========================
    if entry >= recent_high * 0.985:

        acc = detect_accumulation(df)

        # 🔥 thêm filter distance + volume mạnh hơn
        distance = (recent_high - entry) / recent_high

        if vol_ratio >= 1.25 and acc and distance < 0.015:

            sl = entry - atr * 1.3
            risk = entry - sl

            if risk <= 0:
                return None

            score = (
                0.8 +
                vol_compress_score * 0.5 +
                vol_ratio * 1.5 +
                (1 - distance) * 4
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
