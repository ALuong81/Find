def validate_entry(df):

    try:
        # =========================
        # 1. VALIDATE DATA
        # =========================
        if df is None or len(df) < 60:
            return False, None

        required = ["close", "high", "low", "volume"]
        if not all(col in df.columns for col in required):
            return False, None

        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        price = close.iloc[-1]

        # =========================
        # 2. TREND FILTER (QUAN TRỌNG)
        # =========================
        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]
e
        # ❌ loại cổ downtrend
        if price < ma20 or ma20 < ma50:
            return False, None

        # =========================
        # 3. SWING + FIBO
        # =========================
        swing_high = high.tail(20).max()
        swing_low = low.tail(20).min()

        if swing_high <= swing_low:
            return False, None

        range_ = swing_high - swing_low

        entry = swing_high - range_ * 0.382
        entry_deep = swing_high - range_ * 0.5

        sl = swing_low * 0.98   # buffer SL

        tp1 = swing_high
        tp2 = swing_high + range_ * 0.618  # fib extension

        # =========================
        # 4. VOLUME CONFIRM
        # =========================
        vol_now = volume.iloc[-1]
        vol_avg = volume.tail(20).mean()

        if vol_avg == 0:
            return False, None

        vol_ok = vol_now >= vol_avg * 1.2

        # =========================
        # 5. ENTRY LOGIC (MỞ RỘNG)
        # =========================
        near_entry = (
            (price >= entry * 0.97 and price <= entry * 1.03)
            or
            (price >= entry_deep * 0.97 and price <= entry_deep * 1.03)
        )

        if near_entry and vol_ok:

            return True, {
                "entry": entry,
                "sl": sl,
                "tp1": tp1,
                "tp2": tp2
            }

        return False, None

    except Exception as e:
        print("ENTRY ERROR:", str(e))
        return False, None
