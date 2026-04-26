from breakout import breakout_type
from accumulation import detect_accumulation


def entry_score(df, df_h1=None):

    try:
        close = df["close"]
        high = df["high"]
        low = df["low"]

        price = close.iloc[-1]

        swing_high = high.tail(20).max()
        swing_low = low.tail(20).min()

        if swing_high == swing_low:
            return None

        entry = swing_high * 0.98
        sl = swing_low
        tp1 = swing_high
        tp2 = swing_high * 1.1

        score = 0

        # =========================
        # BREAKOUT TYPE
        # =========================
        b_type = breakout_type(df)

        if b_type == "PRE":
            score += 2
        elif b_type == "EARLY":
            score += 1.5
        elif b_type == "STRONG":
            score += 1

        # =========================
        # ACCUMULATION
        # =========================
        if detect_accumulation(df):
            score += 1

        # =========================
        # PRICE POSITION
        # =========================
        if price > swing_high * 0.97:
            score += 1

        return {
            "entry": entry,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "score": score,
            "type": b_type
        }

    except:
        return None
