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
# ENTRY SCORE ENGINE (V7.2 FIX)
# =========================
def entry_score_v7(df):

    if len(df) < 60:
        return None

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # =========================
    # FIX 1: loại bỏ ngày hiện tại khỏi breakout range
    # =========================
    recent_high = high.iloc[-21:-1].max()
    recent_low = low.iloc[-21:-1].min()

    entry = close.iloc[-1]

    vol_mean = volume.rolling(20).mean().iloc[-1]
    vol_std = close.pct_change().rolling(20).std().iloc[-1]

    # =========================
    # BREAKOUT THẬT (NỚI)
    # =========================
    if entry > recent_high * 0.99:
        if volume.iloc[-1] > vol_mean:

            sl = recent_low
            risk = entry - sl

            if risk <= 0:
                return None

            score = (
                (entry / recent_high) +
                (volume.iloc[-1] / vol_mean)
            )

            return {
                "entry": entry,
                "sl": sl,
                "score": score,
                "volatility": vol_std,
                "liquidity": vol_mean,
                "type": "breakout"
            }

    # =========================
    # 🔥 FALLBACK ENTRY (MỞ DÒNG TIỀN)
    # =========================
    if volume.iloc[-1] > vol_mean:

        sl = recent_low
        risk = entry - sl

        if risk <= 0:
            return None

        return {
            "entry": entry,
            "sl": sl,
            "score": 0.5,
            "volatility": vol_std,
            "liquidity": vol_mean,
            "type": "fallback"
        }

    return None
