import numpy as np


def mtf_confirm(df_d, df_h1):

    try:
        if df_h1 is None or len(df_h1) < 50:
            return 0  # 🔥 neutral thay vì False

        # =========================
        # H1 DATA
        # =========================
        close = df_h1["close"]
        high = df_h1["high"]
        vol = df_h1["volume"]

        price = close.iloc[-1]

        # =========================
        # LEVELS
        # =========================
        h1_resistance = high.tail(20).max()

        # =========================
        # VOLUME
        # =========================
        vol_ma = vol.rolling(20).mean().iloc[-1]
        vol_now = vol.iloc[-1]

        # =========================
        # TREND
        # =========================
        ma10 = close.tail(10).mean()

        # =========================
        # 🔥 COMPONENT SCORES
        # =========================

        # 1. BREAKOUT STRENGTH
        break_score = (price / h1_resistance) - 1
        break_score = np.tanh(break_score * 10)  # scale

        # 2. VOLUME CONFIRM
        if vol_ma > 0:
            vol_ratio = vol_now / vol_ma
            vol_score = np.tanh((vol_ratio - 1) * 2)
        else:
            vol_score = 0

        # 3. TREND HOLD
        trend_score = (price / ma10) - 1
        trend_score = np.tanh(trend_score * 8)

        # =========================
        # 🔥 FINAL SCORE
        # =========================
        score = (
            break_score * 1.5 +
            vol_score * 1.2 +
            trend_score * 1.0
        )

        # 🔥 normalize về [-1 → +1]
        score = np.tanh(score)

        return score

    except Exception as e:
        print("MTF ERROR:", str(e))
        return 0
