from breakout import breakout_type
from accumulation import detect_accumulation
from money_flow import money_flow_score
from institutional import institutional_score
from institutional_flow import institutional_flow_score

from early_breakout import detect_early_breakout
from data_loader import load_stock_data_h1


def validate_entry(df, symbol=None, regime="NEUTRAL"):

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

        # =========================
        # BASE LEVEL
        # =========================
        entry = swing_high - (swing_high - swing_low) * 0.382
        sl = swing_low
        tp1 = swing_high
        tp2 = swing_high * 1.1

        # =========================
        # BREAKOUT TYPE
        # =========================
        b_type = breakout_type(df)

        # =========================
        # 🔥 SMART MONEY SCORE (PURE SOFT)
        # =========================
        flow = money_flow_score(df)
        inst = institutional_score(df)
        inst_flow = institutional_flow_score(df)

        sm_score = (
            flow * 1.5 +
            inst * 1.2 +
            inst_flow * 1.8
        )

        # =========================
        # 🔥 REGIME ADJUST (KHÔNG REJECT)
        # =========================
        if regime == "AGGRESSIVE":
            sm_score *= 1.1
        elif regime == "DEFENSIVE":
            sm_score *= 0.8

        # =========================
        # 🔥 CONFIDENCE (NEW)
        # =========================
        confidence = 0.5

        if sm_score > 1:
            confidence += 0.3
        elif sm_score > 0:
            confidence += 0.1
        elif sm_score < -1:
            confidence -= 0.2

        # =========================
        # 🔥 EARLY BREAKOUT H1 (TOP PRIORITY)
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
                            "sm_score": sm_score,
                            "confidence": min(confidence + 0.2, 1)
                        }
            except Exception as e:
                print("H1 ERROR:", str(e))

        # =========================
        # PRE (ưu tiên cao)
        # =========================
        if b_type == "PRE":
            if detect_accumulation(df):
                if price <= swing_high * 1.05:
                    return True, {
                        "entry": price,
                        "sl": sl,
                        "tp1": tp1,
                        "tp2": tp2,
                        "type": "PRE",
                        "sm_score": sm_score,
                        "confidence": confidence
                    }

        # =========================
        # EARLY
        # =========================
        if b_type == "EARLY":
            if entry * 0.9 <= price <= entry * 1.1:
                return True, {
                    "entry": entry,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2,
                    "type": "EARLY",
                    "sm_score": sm_score,
                    "confidence": confidence
                }

        # =========================
        # STRONG
        # =========================
        if b_type == "STRONG":
            if entry * 0.93 <= price <= entry * 1.07:
                return True, {
                    "entry": entry,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2,
                    "type": "STRONG",
                    "sm_score": sm_score,
                    "confidence": confidence
                }

        # =========================
        # FALLBACK PRE
        # =========================
        if b_type is None:
            if detect_accumulation(df):
                return True, {
                    "entry": price,
                    "sl": sl,
                    "tp1": tp1,
                    "tp2": tp2,
                    "type": "PRE",
                    "sm_score": sm_score,
                    "confidence": confidence * 0.9
                }

        # =========================
        # SMART PULLBACK (LUÔN MỞ)
        # =========================
        if entry * 0.85 <= price <= entry * 1.15:
            return True, {
                "entry": price,
                "sl": sl,
                "tp1": tp1,
                "tp2": tp2,
                "type": "PULLBACK",
                "sm_score": sm_score,
                "confidence": confidence * 0.8
            }

        return False, None

    except Exception as e:
        print("ENTRY ERROR:", str(e))
        return False, None
