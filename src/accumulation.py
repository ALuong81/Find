import numpy as np

def detect_accumulation(df):

    try:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        vol = df["volume"]

        if len(df) < 50:
            return False

        # =========================
        # 1. PRICE COMPRESSION
        # =========================
        recent_range = (high.tail(10).max() - low.tail(10).min())
        prev_range = (high.tail(30).max() - low.tail(30).min())

        compression = recent_range < prev_range * 0.6

        # =========================
        # 2. VOLUME DRY
        # =========================
        vol_ma = vol.rolling(20).mean()

        vol_dry = vol.tail(5).mean() < vol_ma.tail(20).mean()

        # =========================
        # 3. HOLD ABOVE MA20
        # =========================
        ma20 = close.rolling(20).mean()

        strong_base = close.iloc[-1] > ma20.iloc[-1]

        # =========================
        # FINAL
        # =========================
        if compression and vol_dry and strong_base:
            return True

        return False

    except:
        return False
