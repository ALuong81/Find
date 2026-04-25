from breakout import breakout_type
from accumulation import detect_accumulation
from money_flow import money_flow_score
from institutional import institutional_score

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

        flow = money_flow_score(df)
        inst = institutional_score(df)

        if flow == 0 or inst == 0:
            return False, None

        # =========================
        # 🔥 EARLY BREAKOUT (H1 trước D1)
        # =========================
        if symbol:
            df_h1 = load_stock_data_h1(symbol)

            if detect_early_breakout(df, df_h1):
                return True, {
                    "entry": price,
                    "sl": swing_low,
                    "tp1": swing_high,
                    "tp2": swing_high * 1.1,
                    "type": "EARLY_BREAKOUT"
                }

        # =========================
        # 🔥 BREAKOUT TYPE
        # =========================
        b_type = breakout_type(df)


        if b_type is None:
            # 🔥 fallback: nếu có accumulation + dòng tiền mạnh
            if detect_accumulation(df):
                if institutional_flow_score(df) > 1:
                    return "PRE"
            

        # PRE
        if b_type == "PRE":
            if detect_accumulation(df) and price <= swing_high * 1.02:
                return True, {
                    "entry": price,
                    "sl": swing_low,
                    "tp1": swing_high,
                    "tp2": swing_high * 1.1,
                    "type": "PRE"
                }

        # EARLY
        if b_type == "EARLY":
            if entry * 0.95 <= price <= entry * 1.05:
                return True, {
                    "entry": entry,
                    "sl": swing_low,
                    "tp1": swing_high,
                    "tp2": swing_high * 1.1,
                    "type": "EARLY"
                }

        # STRONG
        if b_type == "STRONG":
            if entry * 0.98 <= price <= entry * 1.02:
                return True, {
                    "entry": entry,
                    "sl": swing_low,
                    "tp1": swing_high,
                    "tp2": swing_high * 1.1,
                    "type": "STRONG"
                }

        # =========================
        # 🔥 FALLBACK (tăng tín hiệu)
        # =========================
        if price >= swing_low * 1.05:
            return True, {
                "entry": price,
                "sl": swing_low,
                "tp1": swing_high,
                "tp2": swing_high * 1.1,
                "type": "PULLBACK"
            }

        return False, None

    except:
        return False, None
