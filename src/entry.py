from breakout import breakout_type
from accumulation import detect_accumulation
from money_flow import money_flow_score
from institutional import institutional_score
from institutional_flow import institutional_flow_score

from early_breakout import detect_early_breakout
from data_loader import load_stock_data_h1


def validate_entry(df, symbol=None):

    try:
        if df is None or len(df) < 50:
            return False, None

        close = df["close"]
        high = df["high"]
        low = df["low"]

        price = close.iloc[-1]

        swing_high = high.tail(20).max()
        swing_low = low.tail(20).min()

        if swing_high == swing_low:
            return False, None

        entry = swing_high - (swing_high - swing_low) * 0.382
        sl = swing_low
        tp1 = swing_high
        tp2 = swing_high * 1.1

        # =========================
        # 🔥 SMART MONEY FILTER (GIỮ NGUYÊN + FIX)
        # =========================
        flow = money_flow_score(df)
        inst = institutional_score(df)
        inst_flow = institutional_flow_score(df)

        if flow == 0:
            print("DEBUG: no money flow")
            return False, None

        if inst == 0:
            print("DEBUG: no institution")
            return False, None

        if inst_flow < 1:
            print("DEBUG: weak institutional flow")
            return False, None

        # =========================
        # 🔥 EARLY BREAKOUT H1 (NEW)
        # =========================
        if symbol:
            try:
                df_h1 = load_stock_data_h1(symbol)

                if df_h1 is not None and not df_h1.empty:
                    if detect_early_breakout(df, df_h1):
                        return True, {
                            "entry": price,
                            "sl": sl,
                            "tp1": tp1,
                            "tp2": tp2,
                            "type": "EARLY_BREAKOUT"
                        }
            except Exception as e:
                print("H1 ERROR:", str(e))

        # =========================
        # 🔥 BREAKOUT TYPE
        # =========================
        b_type = breakout_type(df)

        # =========================
        # 🔥 FALLBACK PRE (QUAN TRỌNG)
        # =========================
        if b_type is None:
            if detect_accumulation(df) and inst_flow > 1:
                return True, {
                    "entry": price,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2,
                    "type": "PRE"
                }
            return False, None

        # =========================
        # PRE
        # =========================
        if b_type == "PRE":

            if not detect_accumulation(df):
                print("DEBUG: no accumulation")
                return False, None

            if price > swing_high * 1.02:
                print("DEBUG: chasing price")
                return False, None

            return True, {
                "entry": price,
                "sl": sl,
                "tp1": tp1,
                "tp2": tp2,
                "type": "PRE"
            }

        # =========================
        # EARLY (NỚI RANGE)
        # =========================
        if b_type == "EARLY":

            if entry * 0.95 <= price <= entry * 1.05:
                return True, {
                    "entry": entry,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2,
                    "type": "EARLY"
                }

        # =========================
        # STRONG
        # =========================
        if b_type == "STRONG":

            if entry * 0.95 <= price <= entry * 1.05:
                return True, {
                    "entry": entry,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2,
                    "type": "STRONG"
                }

        # =========================
        # 🔥 FALLBACK PULLBACK (TĂNG TẦN SUẤT)
        # =========================
        if price >= swing_low * 1.05:
            return True, {
                "entry": price,
                "sl": sl,
                "tp1": tp1,
                "tp2": tp2,
                "type": "PULLBACK"
            }

        return False, None

    except Exception as e:
        print("ENTRY ERROR:", str(e))
        return False, None
