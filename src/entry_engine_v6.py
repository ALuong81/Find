import numpy as np


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
# ENTRY SCORE ENGINE (V6)
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

        # 🔥 FIX: không kill nữa
        if swing_high <= swing_low:
            swing_high = price * 1.02
            swing_low = price * 0.98

        # =========================
        # ATR
        # =========================
        range_ = (high - low) / close
        atr = range_.rolling(14).mean().iloc[-1]

        # 🔥 FIX: fallback
        if np.isnan(atr) or atr <= 0:
            atr = 0.02

        # =========================
        # ENTRY
        # =========================
        entry = max(price, swing_high * 0.995)

        sl = entry * (1 - atr * 1.8)
        tp1 = entry * (1 + atr * 2.2)
        tp2 = entry * (1 + atr * 3.5)

        # =========================
        # SCORE
        # =========================
        score = 1.0  # 🔥 base score (QUAN TRỌNG)

        # breakout
        try:
            b_type = breakout_type(df)
        except:
            b_type = "UNKNOWN"

        if b_type == "PRE":
            score += 1.5
        elif b_type == "EARLY":
            score += 1.2
        elif b_type == "STRONG":
            score += 1.0
        else:
            score += 0.5

        # accumulation
        try:
            if detect_accumulation(df):
                score += 1.0
        except:
            pass

        # momentum
        ret_3 = close.pct_change(3).iloc[-1]
        ret_5 = close.pct_change(5).iloc[-1]

        momentum = np.tanh((ret_3 + ret_5) * 5)
        score += momentum * 1.2

        # position
        pos = (price - swing_low) / (swing_high - swing_low + 1e-6)
        score += pos * 0.8

        # normalize
        score = score * (1 + np.tanh(score / 3))

        return {
            "entry": float(entry),
            "sl": float(sl),
            "tp1": float(tp1),
            "tp2": float(tp2),
            "score": float(score),
            "type": b_type,
            "volatility": float(atr),
            "liquidity": float(score),
            "correlation": 0.0
        }

    except Exception as e:
        print(f"[ENTRY ERROR] {str(e)}")
        return None
