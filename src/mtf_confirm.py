def mtf_confirm(df_d, df_h1):

    try:
        if df_h1 is None or len(df_h1) < 50:
            return False

        # ===== H1 data =====
        close = df_h1["close"]
        high = df_h1["high"]
        vol = df_h1["volume"]

        # ===== breakout H1 =====
        h1_resistance = high.tail(20).max()
        price = close.iloc[-1]

        # ===== volume =====
        vol_ma = vol.rolling(20).mean()

        # =========================
        # 🔥 LOGIC CONFIRM
        # =========================

        # 1. breakout H1 thật
        cond_break = price >= h1_resistance * 0.98

        # 2. volume xác nhận
        cond_vol = vol.iloc[-1] > vol_ma.iloc[-1] * 1.2

        # 3. giữ trend (không gãy)
        cond_trend = close.iloc[-1] >= close.tail(10).mean()

        if cond_break and cond_vol and cond_trend:
            return True

        return False

    except:
        return False
