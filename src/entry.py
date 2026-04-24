from breakout import early_breakout


def validate_entry(df):

    try:
        # ========= DATA CHECK =========
        if df is None or len(df) < 50:
            print("DEBUG: not enough data")
            return False, None

        required_cols = ["close", "high", "low", "volume"]
        if not all(col in df.columns for col in required_cols):
            print("DEBUG: missing columns")
            return False, None

        close = df["close"]
        high = df["high"]
        low = df["low"]

        price = close.iloc[-1]

        # ========= BREAKOUT =========
        if not early_breakout(df):
            print("DEBUG: no breakout")
            return False, None

        # ========= SWING =========
        swing_high = high.tail(20).max()
        swing_low = low.tail(20).min()

        if swing_high == swing_low:
            print("DEBUG: invalid swing")
            return False, None

        # ========= FIBO =========
        entry = swing_high - (swing_high - swing_low) * 0.382
        sl = swing_low
        tp1 = swing_high
        tp2 = swing_high * 1.1

        lower = entry * 0.95
        upper = entry * 1.05

        print(f"DEBUG: price={round(price,2)} | entry={round(entry,2)}")

        if lower <= price <= upper:
            return True, {
                "entry": round(entry, 2),
                "sl": round(sl, 2),
                "tp1": round(tp1, 2),
                "tp2": round(tp2, 2)
            }

        print("DEBUG: price not in entry zone")
        return False, None

    except Exception as e:
        print("ENTRY ERROR:", e)
        return False, None
