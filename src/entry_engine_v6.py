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
        # fallback nhỏ nhưng không méo RR
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
# ENTRY SCORE ENGINE (V6.1)
# =========================
def entry_score(df, df_h1=None):

    try:
        if len(df) < 50:
            return None

        close = df["close"]
        high = df["high"]
        low = df["low"]

        price = close.iloc[-1]

        # =========================
        # STRUCTURE
        # =========================
        swing_high = high.tail(20).max()
        swing_low = low.tail(20).min()

        if swing_high <= swing_low:
            return None

        # =========================
        # ATR
        # =========================
        range_ = (high - low) / close
        atr = range_.rolling(14).mean().iloc[-1]

        if np.isnan(atr) or atr <= 0:
            atr = 0.02

        # =========================
        # ENTRY / SL / TP
        # =========================
        entry = max(price, swing_high * 0.995)
        sl = entry * (1 - atr * 1.8)
        tp1 = entry * (1 + atr * 1.8)

        # =========================
        # SCORING (REBALANCED)
        # =========================
        score = 0.0

        # -------------------------
        # BREAKOUT
        # -------------------------
        b_type = breakout_type(df)

        if b_type == "PRE":
            score += 1.5
        elif b_type == "EARLY":
            score += 1.2
        elif b_type == "STRONG":
            score += 1.0
        else:
            score += 0.6

        # -------------------------
        # ACCUMULATION
        # -------------------------
        if detect_accumulation(df):
            score += 1.0

        # -------------------------
        # PRICE POSITION
        # -------------------------
        pos = (price - swing_low) / (swing_high - swing_low + 1e-6)

        if pos > 0.85:
            score += 1.0
        elif pos > 0.7:
            score += 0.7
        elif pos > 0.55:
            score += 0.4

        # -------------------------
        # MOMENTUM (CLIPPED)
        # -------------------------
        ret_3 = close.pct_change(3).iloc[-1]
        ret_5 = close.pct_change(5).iloc[-1]

        momentum = (ret_3 + ret_5)

        # 🔥 clamp tránh kéo âm quá mạnh
        momentum = max(-0.05, min(momentum, 0.1))

        score += momentum * 5

        # -------------------------
        # VOLUME
        # -------------------------
        if "volume" in df:
            vol = df["volume"]
            vol_mean = vol.rolling(20).mean().iloc[-1]
            vol_now = vol.iloc[-1]

            if vol_mean > 0:
                vol_ratio = vol_now / vol_mean

                if vol_ratio > 1.5:
                    score += 1.0
                elif vol_ratio > 1.2:
                    score += 0.6
                elif vol_ratio > 1.0:
                    score += 0.3

        # -------------------------
        # FLOOR (QUAN TRỌNG)
        # -------------------------
        score = max(score, 0.3)

        # =========================
        # OUTPUT
        # =========================
        return {
            "entry": float(entry),
            "sl": float(sl),
            "tp1": float(tp1),
            "score": float(score),
            "type": b_type,
            "volatility": float(atr),
            "liquidity": float(score),
            "correlation": 0.0
        }

    except Exception as e:
        print(f"[ENTRY ERROR] {str(e)}")
        return None
