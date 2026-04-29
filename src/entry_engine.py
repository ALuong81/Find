import numpy as np

from breakout import breakout_type
from accumulation import detect_accumulation


# =========================
# ENTRY SCORE ENGINE (V2)
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
        # ATR (anti RR ảo)
        # =========================
        range_ = (high - low) / close
        atr = range_.rolling(14).mean().iloc[-1]

        # fallback tránh NaN
        if np.isnan(atr) or atr <= 0:
            atr = 0.02

        # =========================
        # ENTRY / SL / TP
        # =========================
        entry = max(price, swing_high * 0.99)

        sl = entry * (1 - atr * 2)
        tp1 = entry * (1 + atr * 2.5)
        tp2 = entry * (1 + atr * 4)

        # =========================
        # SCORING
        # =========================
        score = 0

        # -------------------------
        # BREAKOUT TYPE
        # -------------------------
        b_type = breakout_type(df)

        if b_type == "PRE":
            score += 2.0
        elif b_type == "EARLY":
            score += 1.5
        elif b_type == "STRONG":
            score += 1.0
        else:
            score += 0.5

        # -------------------------
        # ACCUMULATION
        # -------------------------
        if detect_accumulation(df):
            score += 1.2

        # -------------------------
        # PRICE POSITION
        # -------------------------
        pos = (price - swing_low) / (swing_high - swing_low + 1e-6)

        if pos > 0.9:
            score += 1.2
        elif pos > 0.75:
            score += 0.8
        elif pos > 0.6:
            score += 0.4

        # -------------------------
        # MOMENTUM
        # -------------------------
        ret_3 = close.pct_change(3).iloc[-1]
        ret_5 = close.pct_change(5).iloc[-1]

        momentum = np.tanh((ret_3 + ret_5) * 5)
        score += momentum * 1.5

        # -------------------------
        # VOLUME (liquidity proxy)
        # -------------------------
        if "volume" in df:
            vol = df["volume"]
            vol_mean = vol.rolling(20).mean().iloc[-1]
            vol_now = vol.iloc[-1]

            if vol_mean > 0:
                vol_boost = (vol_now / vol_mean) - 1
                score += np.tanh(vol_boost) * 1.0

        # -------------------------
        # NORMALIZE SCORE
        # -------------------------
        score = score * (1 + np.tanh(score / 3))

        # =========================
        # EXTRA FEATURES FOR META
        # =========================
        volatility = float(atr)
        liquidity = float(score)  # proxy
        correlation = 0.0  # sẽ set bên ngoài nếu có RS

        return {
            "entry": float(entry),
            "sl": float(sl),
            "tp1": float(tp1),
            "tp2": float(tp2),
            "score": float(score),
            "type": b_type,
            "volatility": volatility,
            "liquidity": liquidity,
            "correlation": correlation
        }

    except Exception as e:
        print(f"[ENTRY ERROR] {str(e)}")
        return None
