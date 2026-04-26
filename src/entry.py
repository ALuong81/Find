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
        # 🔥 SMART MONEY SCORE (SOFT)
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
        # 🔥 REGIME ADJUST
        # =========================
        if regime == "AGGRESSIVE":
            sm_score *= 1.1
        elif regime == "DEFENSIVE":
            sm_score *= 0.8

        # =========================
        # 🔥 CONFIDENCE (SOFT)
        # =========================
        confidence = 0.5

        if sm_score > 1:
            confidence += 0.3
        elif sm_score > 0:
            confidence += 0.1
        elif sm_score < -1:
            confidence -= 0.25  # 🔥 tăng penalty

        # =========================
        # 🔥 TYPE DEFAULT
        # =========================
        final_type = "PULLBACK"

        # =========================
        # 🔥 EARLY BREAKOUT H1 (TOP PRIORITY)
        # =========================
        if symbol:
            try:
                df_h1 = load_stock_data_h1(symbol)

                if df_h1 is not None and len(df_h1) > 20:
                    if detect_early_breakout(df, df_h1):
                        final_type = "EARLY_BREAKOUT"
                        confidence += 0.25
            except Exception as e:
                print("H1 ERROR:", str(e))

        # =========================
        # TYPE LOGIC (KHÔNG REJECT)
        # =========================
        if b_type == "PRE":
            if detect_accumulation(df):
                if price <= swing_high * 1.05:
                    final_type = "PRE"
                    confidence += 0.15

        elif b_type == "EARLY":
            if entry * 0.9 <= price <= entry * 1.1:
                final_type = "EARLY"
                confidence += 0.1

        elif b_type == "STRONG":
            if entry * 0.93 <= price <= entry * 1.07:
                final_type = "STRONG"
                confidence += 0.05

        elif b_type is None:
            if detect_accumulation(df):
                final_type = "PRE"
                confidence += 0.05

        # =========================
        # 🔥 PENALTY ZONE (THAY VÌ REJECT)
        # =========================
        if not (entry * 0.85 <= price <= entry * 1.15):
            confidence -= 0.2

        # clamp confidence
        confidence = max(0, min(confidence, 1))

        # =========================
        # 🔥 FINAL OUTPUT (LUÔN RETURN)
        # =========================
        return True, {
            "entry": price if final_type in ["PRE", "PULLBACK", "EARLY_BREAKOUT"] else entry,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "type": final_type,
            "sm_score": sm_score,
            "confidence": confidence
        }

    except Exception as e:
        print("ENTRY ERROR:", str(e))
        return False, None
