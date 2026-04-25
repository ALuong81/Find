def detect_early_breakout(df_d, df_h1):

    try:
        if df_d is None or df_h1 is None:
            return False

        if len(df_d) < 30 or len(df_h1) < 50:
            return False

        # ===== D1 =====
        high_d = df_d["high"]
        close_d = df_d["close"]

        d_resistance = high_d.tail(20).max()
        d_price = close_d.iloc[-1]

        # D1 chưa breakout
        if d_price >= d_resistance * 0.98:
            return False

        # ===== H1 =====
        high_h1 = df_h1["high"]
        close_h1 = df_h1["close"]
        vol_h1 = df_h1["volume"]

        h1_res = high_h1.tail(20).max()
        h1_price = close_h1.iloc[-1]

        vol_ma = vol_h1.rolling(20).mean()

        cond_break = h1_price >= h1_res * 0.99
        cond_vol = vol_h1.iloc[-1] > vol_ma.iloc[-1] * 1.2
        cond_trend = close_h1.iloc[-1] >= close_h1.tail(10).mean()

        return cond_break and cond_vol and cond_trend

    except:
        return False
