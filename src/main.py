from symbol_loader import load_symbols
from data_loader import load_stock_data, load_index, load_stock_data_h1

from smart_money import (
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
# 🔥 MARKET REGIME (SOFT)
# =========================
def market_regime(df_index):

    try:
        close = df_index["close"]

        ret_5 = close.pct_change(5).iloc[-1]
        ret_20 = close.pct_change(20).iloc[-1]
        vol = close.pct_change().rolling(20).std().iloc[-1]

        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]

        trend = 1 if ma20 > ma50 else -1

        score = (
            ret_5 * 2 +
            ret_20 * 1.5 -
            vol * 2 +
            trend
        )

        score = np.tanh(score * 3)

        if score > 0.3:
            return "AGGRESSIVE", score
        elif score > -0.3:
            return "NEUTRAL", score
        else:
            return "DEFENSIVE", score

    except:
        return "DEFENSIVE", -1


# =========================
# 🔥 REGIME CONFIG (KEY V4)
# =========================
def regime_config(mode):

    if mode == "AGGRESSIVE":
        return {
            "rs_threshold": -0.12,
            "position_scale": 1.0,
            "score_boost": 1.2
        }

    if mode == "NEUTRAL":
        return {
            "rs_threshold": -0.07,
            "position_scale": 0.7,
            "score_boost": 1.0
        }

    # DEFENSIVE
    return {
        "rs_threshold": -0.03,
        "position_scale": 0.4,
        "score_boost": 0.8
    }


# =========================
# MAIN
# =========================
def main():

    print("🚀 START BOT V4")

    df_symbols = load_symbols()
    print("TOTAL SYMBOLS:", len(df_symbols))

    # =========================
    # 🔥 MARKET (NO MORE STOP)
    # =========================
    df_index = load_index()

    mode, m_score = market_regime(df_index)
    cfg = regime_config(mode)

    print("⚙️ MODE:", mode, "| score:", round(m_score, 3))

    # ❌ KHÔNG STOP nữa
    if mode == "DEFENSIVE":
        print("⚠️ DEFENSIVE MODE → giảm risk, không tắt bot")

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
    # 🔥 FILTER + SCORING
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

            # 🔥 adaptive RS theo regime
            if rs < cfg["rs_threshold"]:
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
    # ENTRY
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
            # MTF SOFT
            # =========================
            try:
                df_h1 = load_stock_data_h1(symbol)
                mtf_ok = mtf_confirm(df, df_h1) if df_h1 is not None else True
            except:
                mtf_ok = True

            if not mtf_ok:
                print("   ⚠️ MTF WEAK")

            rr = (f["tp1"] - f["entry"]) / (f["entry"] - f["sl"])

            score = rr

            type_weight = {
                "EARLY_BREAKOUT": 1.8,
                "PRE": 1.6,
                "EARLY": 1.3,
                "STRONG": 1.0,
                "PULLBACK": 1.1
            }

            score *= type_weight.get(f["type"], 1.0)

            system_score = next((x[1] for x in scored if x[0] == symbol), 0)

            final_score = score * (1 + system_score * 0.1)

            # 🔥 regime scaling
            final_score *= cfg["score_boost"]

            signals.append({
                "symbol": symbol,
                "entry": f["entry"],
                "sl": f["sl"],
                "tp1": f["tp1"],
                "tp2": f["tp2"],
                "rr": rr,
                "type": f["type"],
                "score": final_score,
                "risk_scale": cfg["position_scale"]
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

        msg = f"🔥 V4 SIGNALS | MODE: {mode}\n\n"

        for s in signals:
            msg += (
                f"{s['symbol']} ({s['type']})\n"
                f"Entry: {round(s['entry'],2)}\n"
                f"SL: {round(s['sl'],2)}\n"
                f"TP1: {round(s['tp1'],2)}\n"
                f"RR: {round(s['rr'],2)}\n"
                f"Risk: x{s['risk_scale']}\n\n"
            )

        send_telegram(msg)

    else:
        print("⚠️ NO SIGNAL")


if __name__ == "__main__":
    main()
