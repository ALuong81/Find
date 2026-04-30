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

        # STRUCTURE (robust)

        # =========================

        swing_high = high.tail(20).max()

        swing_low = low.tail(20).min()

        if swing_high <= swing_low:

            swing_high = price * 1.02

            swing_low = price * 0.98

        # =========================

        # ATR (true range)

        # =========================

        tr = np.maximum(

            high - low,

            np.maximum(

                abs(high - close.shift()),

                abs(low - close.shift())

            )

        )

        atr = tr.rolling(14).mean().iloc[-1]

        if np.isnan(atr) or atr <= 0:

            atr = price * 0.02

        atr_pct = atr / price

        # =========================

        # BREAKOUT STRENGTH

        # =========================

        breakout_strength = (price - swing_high) / (atr + 1e-6)

        # range expansion

        range_now = (high.iloc[-1] - low.iloc[-1]) / price

        range_mean = ((high - low) / close).rolling(20).mean().iloc[-1]

        expansion = range_now / (range_mean + 1e-6)

        # =========================

        # VOLUME CONFIRM

        # =========================

        vol_score = 0

        if "volume" in df:

            vol = df["volume"]

            vol_mean = vol.rolling(20).mean().iloc[-1]

            vol_now = vol.iloc[-1]

            if vol_mean > 0:

                vol_ratio = vol_now / vol_mean

                vol_score = np.tanh(vol_ratio - 1)

        # =========================

        # FALSE BREAKOUT FILTER

        # =========================

        false_breakout = 0

        # wick lớn (bị đạp xuống)

        upper_wick = high.iloc[-1] - max(open := close.iloc[-2], close.iloc[-1])

        body = abs(close.iloc[-1] - open)

        if body > 0:

            wick_ratio = upper_wick / body

            if wick_ratio > 1.5:

                false_breakout = 1

        # =========================

        # MOMENTUM

        # =========================

        ret_3 = close.pct_change(3).iloc[-1]

        ret_5 = close.pct_change(5).iloc[-1]

        momentum = np.tanh((ret_3 + ret_5) * 4)

        # =========================

        # POSITION IN RANGE

        # =========================

        pos = (price - swing_low) / (swing_high - swing_low + 1e-6)

        # =========================

        # ACCUMULATION

        # =========================

        acc_score = 0

        try:

            if detect_accumulation(df):

                acc_score = 1

        except:

            pass

        # =========================

        # SCORE BUILD

        # =========================

        score = 1.0  # base

        score += breakout_strength * 1.2

        score += np.tanh(expansion - 1) * 1.0

        score += vol_score * 1.2

        score += momentum * 1.5

        score += pos * 0.8

        score += acc_score * 1.0

        # penalty false breakout

        if false_breakout:

            score *= 0.6

        # normalize

        score = score * (1 + np.tanh(score / 3))

        # =========================

        # ENTRY / SL / TP

        # =========================

        entry = max(price, swing_high * 0.995)

        sl = entry - atr * 1.8

        tp1 = entry + atr * 2.2

        tp2 = entry + atr * 3.5

        # =========================

        # EXTRA FEATURES

        # =========================

        volatility = float(atr_pct)

        liquidity = float(vol_score)

        correlation = 0.0

        return {

            "entry": float(entry),

            "sl": float(sl),

            "tp1": float(tp1),

            "tp2": float(tp2),

            "score": float(score),

            "type": "BREAKOUT_V6.1",

            "volatility": volatility,

            "liquidity": liquidity,

            "correlation": correlation

        }

    except Exception as e:

        print(f"[ENTRY ERROR] {str(e)}")

        return None
