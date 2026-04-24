from breakout import early_breakout

def validate_entry(df):

    try:
        if df is None or len(df) < 50:
            return False, None

        if not all(col in df.columns for col in ["close", "high", "low"]):
            return False, None

        # 🔥 breakout sớm (lọc trước)
        if not early_breakout(df):
            return False, None

        close = df["close"]
        high = df["high"]
        low = df["low"]

        swing_high = high.tail(20).max()
        swing_low = low.tail(20).min()

        if swing_high == swing_low:
            return False, None

        entry = swing_high - (swing_high - swing_low) * 0.382
        sl = swing_low
        tp1 = swing_high
        tp2 = swing_high * 1.1

        price = close.iloc[-1]

        if entry * 0.95 <= price <= entry * 1.05:

            return True, {
                "entry": entry,
                "sl": sl,
                "tp1": tp1,
                "tp2": tp2
            }

        return False, None

    except:
        return False, None
