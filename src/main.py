from symbol_loader import load_symbols
from data_loader import load_stock_data, load_index, load_stock_data_h1

from smart_money import (
    market_score,
    sector_money_flow,
    pick_leaders
)

from sector_rotation import sector_rotation
from relative_strength import relative_strength
from entry import validate_entry
from voe import voe_score
from accumulation import detect_accumulation

from institutional import institutional_score
from institutional_flow import institutional_flow_score
from money_flow import money_flow_score
from flow_timeline import flow_timeline

from mtf_confirm import mtf_confirm
from tracker import log_trade

import os
import requests
import numpy as np


# =========================
# TELEGRAM
# =========================
def send_telegram(msg):

    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("⚠️ TELEGRAM NOT CONFIG")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": chat_id,
            "text": msg
        })
    except Exception as e:
        print("❌ TELEGRAM ERROR:", str(e))


# =========================
# 🔥 V4 MARKET REGIME (ML STYLE)
# =========================
def market_regime(df_index):

    try:
        close = df_index["close"]

        ret_5 = close.pct_change(5).iloc[-1]
        ret_20 = close.pct_change(20).iloc[-1]

        vol = close.pct_change().rolling(20).std().iloc[-1]

        trend = close.rolling(20).mean().iloc[-1] - close.rolling(50).mean().iloc[-1]

        score = (
            ret_5 * 2 +
            ret_20 * 1.5 -
            vol * 2 +
            (1 if trend > 0 else -1)
        )

        # 🔥 normalize
        score = np.tanh(score * 3)

        if score > 0.3:
            return "AGGRESSIVE", score
        elif score > -0.2:
            return "NEUTRAL", score
        else:
            return "DEFENSIVE", score

    except:
        return "DEFENSIVE", -1


# =========================
# MAIN
# =========================
def main():

    print("🚀 START BOT V4")

    df_symbols = load_symbols()
    print("TOTAL SYMBOLS:", len(df_symbols))

    # =========================
    # 🔥 MARKET V4
    # =========================
    df_index = load_index()

    mode, m_score = market_regime(df_index)

    print("⚙️ MODE:", mode, "| score:", round(m_score, 3))

    if mode == "DEFENSIVE":
        print("❌ MARKET DEFENSIVE → STOP")
        return

    # =========================
    # SECTOR
    # =========================
    sector_df = sector_money_flow(df_symbols)
    sector_df = sector_rotation(sector_df)

    top_sectors = sector_df.head(3)

    print("\n🔥 TOP SECTORS:")
    for _, row in top_sectors.iterrows():
        print(f"{row['sector']} | score={round(row['rotation_score'],2)}")

    # =========================
    # LEADERS RAW
    # =========================
    leaders = []

    for _, row in top_sectors.iterrows():
        stocks = pick_leaders(df_symbols, row["sector"])
        for _, s in stocks.iterrows():
            leaders.append(s["symbol"])

    leaders = list(set(leaders))
    print("\n🔥 RAW LEADERS:", leaders)

    # =========================
    # 🔥 FILTER + SCORING V4
    # =========================
    scored = []

    for symbol in leaders:
        try:
            df = load_stock_data(symbol)

            rs = relative_strength(df, df_index)
            voe = voe_score(df, df_index)
            inst = institutional_score(df)
            inst_flow = institutional_flow_score(df)
            mf = money_flow_score(df)
            acc = detect_accumulation(df)
            flow_acc = flow_timeline(df)

            # 🔥 adaptive RS filter
            if mode == "AGGRESSIVE":
                if rs < -0.12:
                    continue
            else:
                if rs < -0.05:
                    continue

            score = (
                rs * 2 +
                voe * 1.5 +
                inst * 1.2 +
                inst_flow * 1.8 +
                mf * 1.3 +
                flow_acc * 1.2 +
                (1 if acc else 0)
            )

            # 🔥 nonlinear boost
            score *= (1 + np.tanh(score))

            scored.append((symbol, score))

        except Exception as e:
            print(symbol, "FILTER ERROR:", str(e))

    scored = sorted(scored, key=lambda x: x[1], reverse=True)

    if not scored:
        print("⚠️ NO LEADER → fallback")
        leaders = leaders[:10]
    else:
        leaders = [s[0] for s in scored[:12]]

    print("\n🔥 STRONG LEADERS:", leaders)

    # =========================
    # 🔥 ENTRY V4
    # =========================
    print("\nSCAN ENTRY...\n")

    signals = []

    for symbol in leaders:

        try:
            df = load_stock_data(symbol)
            price = df["close"].iloc[-1]

            ok, f = validate_entry(df, symbol)

            print(f"{symbol} | price={round(price,2)} | type={f['type'] if f else None}")

            if not ok:
                print("   ❌ skip")
                continue

            # =========================
            # 🔥 SOFT MTF CONFIRM
            # =========================
            try:
                df_h1 = load_stock_data_h1(symbol)
                mtf_ok = mtf_confirm(df, df_h1) if df_h1 is not None else True
            except:
                mtf_ok = True

            # 🔥 KHÔNG kill signal
            if not mtf_ok:
                print("   ⚠️ MTF WEAK (not rejected)")

            rr = (f["tp1"] - f["entry"]) / (f["entry"] - f["sl"])

            # =========================
            # 🔥 SIGNAL SCORE V4
            # =========================
            score = rr

            type_weight = {
                "EARLY_BREAKOUT": 1.8,
                "PRE": 1.6,
                "EARLY": 1.3,
                "STRONG": 1.0,
                "PULLBACK": 1.1
            }

            score *= type_weight.get(f["type"], 1.0)

            # 🔥 combine with system strength
            system_score = next((x[1] for x in scored if x[0] == symbol), 0)

            final_score = score * (1 + system_score * 0.1)

            # 🔥 regime boost
            if mode == "AGGRESSIVE":
                final_score *= 1.2

            signals.append({
                "symbol": symbol,
                "entry": f["entry"],
                "sl": f["sl"],
                "tp1": f["tp1"],
                "tp2": f["tp2"],
                "rr": rr,
                "type": f["type"],
                "score": final_score
            })

            log_trade(symbol, f["entry"], f["sl"], f["tp1"])

            print("   ✅ SIGNAL")

        except Exception as e:
            print(symbol, "ERROR:", str(e))

    signals = sorted(signals, key=lambda x: x["score"], reverse=True)

    print("\nTOTAL SIGNAL:", len(signals))

    # =========================
    # TELEGRAM
    # =========================
    if signals:

        msg = "🔥 V4 SMART MONEY SIGNALS\n\n"

        for s in signals:
            msg += (
                f"{s['symbol']} ({s['type']})\n"
                f"Entry: {round(s['entry'],2)}\n"
                f"SL: {round(s['sl'],2)}\n"
                f"TP1: {round(s['tp1'],2)}\n"
                f"RR: {round(s['rr'],2)}\n\n"
            )

        send_telegram(msg)

    else:
        print("⚠️ NO SIGNAL")


if __name__ == "__main__":
    main()
