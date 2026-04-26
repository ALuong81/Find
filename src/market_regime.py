import pandas as pd


def detect_market_regime(df_index):

    try:
        if df_index is None or len(df_index) < 60:
            return "SIDEWAY"

        df = df_index.copy()

        # =========================
        # 🔥 PRICE + TREND
        # =========================
        close = df["close"]

        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]

        trend = 1 if ma20 > ma50 else -1

        # =========================
        # 🔥 MOMENTUM
        # =========================
        ret_5 = close.pct_change(5).iloc[-1]
        ret_20 = close.pct_change(20).iloc[-1]

        momentum = (ret_5 * 0.6) + (ret_20 * 0.4)

        # =========================
        # 🔥 VOLATILITY (CHUẨN)
        # =========================
        vol_price = close.pct_change().rolling(20).std().iloc[-1]

        # normalize nhẹ
        if pd.isna(vol_price):
            vol_price = 0

        # =========================
        # 🔥 VOLUME FLOW (SMOOTH)
        # =========================
        vol = df["volume"]

        vol_ma20 = vol.rolling(20).mean().iloc[-1]
        vol_ma5 = vol.rolling(5).mean().iloc[-1]

        if pd.isna(vol_ma20) or vol_ma20 == 0:
            vol_ratio = 1
        else:
            vol_ratio = vol_ma5 / vol_ma20

        # clamp tránh spike
        vol_ratio = max(min(vol_ratio, 2), 0.5)

        # =========================
        # 🔥 SCORE TỔNG HỢP
        # =========================
        score = (
            momentum * 2 +
            trend * 0.8 +
            (vol_ratio - 1) * 0.5 -
            vol_price * 1.2
        )

        # =========================
        # 🔥 CLASSIFY REGIME
        # =========================
        if score > 0.5:
            return "TREND_STRONG"

        elif score > 0.1:
            return "TREND_WEAK"

        elif score > -0.4:
            return "SIDEWAY"

        else:
            return "DISTRIBUTION"

    except Exception as e:
        print("REGIME ERROR:", str(e))
        return "SIDEWAY"
