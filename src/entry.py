from breakout import breakout_type
from accumulation import detect_accumulation
from money_flow import money_flow_score
from institutional import institutional_score


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

        if swing_high == swing_low:
            return False, None

        entry = swing_high - (swing_high - swing_low) * 0.382
        sl = swing_low
        tp1 = swing_high
        tp2 = swing_high * 1.1

        price = close.iloc[-1]

        # =========================
        # 🔥 SMART FILTER
        # =========================
        flow = money_flow_score(df)
        inst = institutional_score(df)

        if flow == 0:
            print("DEBUG: no money flow")
            return False, None

        if inst == 0:
            print("DEBUG: no institution")
            return False, None

        # =========================
        # 🔥 ENTRY LOGIC
        # =========================

        # PRE breakout → vào sớm (NHƯNG phải tích lũy + không quá xa)
        if b_type == "PRE":

            if not detect_accumulation(df):
                print("DEBUG: no accumulation")
                return False, None

            # tránh mua đuổi
            if price > swing_high * 1.02:
                print("DEBUG: chasing price")
                return False, None

            return True, {
                "entry": price,
                "sl": sl,
                "tp1": tp1,
                "tp2": tp2,
                "type": "PRE",
                "flow": flow,
                "inst": inst
            }

        # EARLY → vùng pullback đẹp nhất
        if b_type == "EARLY":

            if entry * 0.97 <= price <= entry * 1.03:
                return True, {
                    "entry": entry,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2,
                    "type": "EARLY",
                    "flow": flow,
                    "inst": inst
                }

        # STRONG → breakout xác nhận
        if b_type == "STRONG":

            if entry * 0.98 <= price <= entry * 1.02:
                return True, {
                    "entry": entry,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2,
                    "type": "STRONG",
                    "flow": flow,
                    "inst": inst
                }

        return False, None

    except Exception as e:
        print("ENTRY ERROR:", str(e))
        return False, None
