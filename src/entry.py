from breakout import breakout_type
from accumulation import detect_accumulation

def validate_entry(df):

    try:
        if df is None or len(df) < 50:
            return False, None

        close = df["close"]
        high = df["high"]
        low = df["low"]

        b_type = breakout_type(df)

        if b_type is None:
            return False, None

        swing_high = high.tail(20).max()
        swing_low = low.tail(20).min()

        entry = swing_high - (swing_high - swing_low) * 0.382
        sl = swing_low
        tp1 = swing_high
        tp2 = swing_high * 1.1

        price = close.iloc[-1]

        # 🔥 PRE breakout + accumulation
        if b_type == "PRE":
            if detect_accumulation(df):
                return True, {
                    "entry": price,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2
                }

        # EARLY
        if b_type == "EARLY":
            if price >= entry * 0.95 and price <= entry * 1.05:
                return True, {
                    "entry": entry,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2
                }

        # STRONG
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
