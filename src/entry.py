from breakout import breakout_type

def validate_entry(df):

    try:
        if df is None or len(df) < 50:
            return False, None

        if not all(col in df.columns for col in ["close", "high", "low"]):
            return False, None

        close = df["close"]
        high = df["high"]
        low = df["low"]

        # 🔥 breakout check
        b_type = breakout_type(df)
        if b_type is None:
            return False, None

        swing_high = high.tail(20).max()
        swing_low = low.tail(20).min()

        if swing_high == swing_low:
            return False, None

        entry = swing_high - (swing_high - swing_low) * 0.382
        sl = swing_low
        tp1 = swing_high
        tp2 = swing_high * 1.1

        price = close.iloc[-1]

        # 🔥 entry zone rộng hơn cho EARLY
        if b_type == "EARLY":
            if price >= entry * 0.95 and price <= entry * 1.05:
                return True, {
                    "entry": entry,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2
                }

        # 🔥 STRONG stricter
        if b_type == "STRONG":
            if price >= entry * 0.98 and price <= entry * 1.02:
                return True, {
                    "entry": entry,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2
                }

        return False, None

    except:
        return False, None
