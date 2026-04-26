import numpy as np


def mtf_confirm(df_d, df_h1):

    try:
        # =========================
        # NO DATA → NEUTRAL
        # =========================
        if df_h1 is None or len(df_h1) < 50:
            return 0.0

        close = df_h1["close"]
        high = df_h1["high"]
        vol = df_h1["volume"]

        price = close.iloc[-1]

        # =========================
        # LEVELS
        # =========================
        h1_resistance = high.tail(20).max()

        if h1_resistance <= 0:
            return 0.0

        # =========================
        # VOLUME
        # =========================
        vol_ma = vol.rolling(20).mean().iloc[-1]
        vol_now = vol.iloc[-1]

        # =========================
        # TREND
        # =========================
        ma10 = close.rolling(10).mean().iloc[-1]

        # =========================
        # 🔥 COMPONENT 1: BREAKOUT QUALITY
        # =========================
        break_raw = (price / h1_resistance) - 1
        break_score = np.tanh(break_raw * 8)

        # =========================
        # 🔥 COMPONENT 2: VOLUME CONFIRM
        # =========================
        if vol_ma > 0:
            vol_ratio = vol_now / vol_ma
            vol_score = np.tanh((vol_ratio - 1) * 1.5)
        else:
            vol_score = 0.0

        # =========================
        # 🔥 COMPONENT 3: TREND HOLD
        # =========================
        if ma10 > 0:
            trend_raw = (price / ma10) - 1
            trend_score = np.tanh(trend_raw * 6)
        else:
            trend_score = 0.0

        # =========================
        # 🔥 RAW SCORE
        # =========================
        score = (
            break_score * 1.4 +
            vol_score * 1.2 +
            trend_score * 1.0
        )

        # =========================
        # 🔥 SMOOTH (GIẢM NOISE)
        # =========================
        # EMA-like smoothing bằng rolling mean nhẹ
        recent = close.pct_change().tail(5).mean()

        if not np.isnan(recent):
            score += np.tanh(recent * 5) * 0.5

        # =========================
        # 🔥 FINAL NORMALIZE
        # =========================
        score = np.tanh(score)

        return float(score)

    except Exception as e:
        print("MTF ERROR:", str(e))
        return 0.0
