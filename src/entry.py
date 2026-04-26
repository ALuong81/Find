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
        # 🔥 SMART MONEY FILTER (NỚI NHẸ)
        # =========================
        flow = money_flow_score(df)
        inst = institutional_score(df)
        inst_flow = institutional_flow_score(df)

        # ❗ nới điều kiện để không bị "tắt hệ"
        if flow <= 0:
            print("DEBUG: weak flow")
            return False, None

        if inst < 0:
            print("DEBUG: weak institution")
            return False, None

        # 🔥 không chặn cứng nữa
        strong_inst = inst_flow >= 1

        # =========================
        # 🔥 EARLY BREAKOUT H1 (ƯU TIÊN CAO)
        # =========================
        if symbol:
            try:
                df_h1 = load_stock_data_h1(symbol)

                if df_h1 is not None and len(df_h1) > 20:
                    if detect_early_breakout(df, df_h1):
                        return True, {
                            "entry": price,
                            "sl": sl,
                            "tp1": tp1,
                            "tp2": tp2,
                            "type": "EARLY_BREAKOUT",
                            "flow": flow,
                            "inst": inst
                        }
            except Exception as e:
                print("H1 ERROR:", str(e))

        # =========================
        # 🔥 BREAKOUT TYPE
        # =========================
        b_type = breakout_type(df)

        # =========================
        # 🔥 PRE (ưu tiên trước fallback)
        # =========================
        if b_type == "PRE":

            if detect_accumulation(df):

                if price <= swing_high * 1.03:  # 🔥 nới nhẹ
                    return True, {
                        "entry": price,
                        "sl": sl,
                        "tp1": tp1,
                        "tp2": tp2,
                        "type": "PRE",
                        "flow": flow,
                        "inst": inst
                    }

        # =========================
        # 🔥 EARLY
        # =========================
        if b_type == "EARLY":

            if entry * 0.93 <= price <= entry * 1.07:  # 🔥 nới mạnh
                return True, {
                    "entry": entry,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2,
                    "type": "EARLY",
                    "flow": flow,
                    "inst": inst
                }

        # =========================
        # 🔥 STRONG
        # =========================
        if b_type == "STRONG":

            if entry * 0.95 <= price <= entry * 1.05:
                return True, {
                    "entry": entry,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2,
                    "type": "STRONG",
                    "flow": flow,
                    "inst": inst
                }

        # =========================
        # 🔥 FALLBACK PRE (QUAN TRỌNG)
        # =========================
        if b_type is None:

            if detect_accumulation(df) and strong_inst:
                return True, {
                    "entry": price,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2,
                    "type": "PRE",
                    "flow": flow,
                    "inst": inst
                }

        # =========================
        # 🔥 SMART PULLBACK (FIX NGU)
        # =========================
        # chỉ pullback nếu gần vùng entry
        if entry * 0.9 <= price <= entry * 1.1:

            if flow > 0 and inst >= 0:
                return True, {
                    "entry": price,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2,
                    "type": "PULLBACK",
                    "flow": flow,
                    "inst": inst
                }

        return False, None

    except Exception as e:
        print("ENTRY ERROR:", str(e))
        return False, None
