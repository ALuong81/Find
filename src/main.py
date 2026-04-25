from symbol_loader import load_symbols
from data_loader import load_stock_data, load_index

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
from money_flow import money_flow_score
from flow_timeline import flow_timeline
from market_mode import get_market_mode

from tracker import log_trade

import os
import requests
import datetime


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
# SESSION DETECT
# =========================
def get_session():

    hour = datetime.datetime.utcnow().hour + 7

    if hour < 11:
        return "MORNING"
    elif hour < 14:
        return "MID"
    else:
        return "CLOSE"


# =========================
# MAIN
# =========================
def main():

    print("🚀 START BOT")

    session = get_session()
    print("🕒 SESSION:", session)

    df_symbols = load_symbols()
    print("TOTAL SYMBOLS:", len(df_symbols))

    # ===== MARKET =====
    m = market_score()
    print("MARKET SCORE:", m)

    mode = get_market_mode(m)
    print("⚙️ MODE:", mode)

    if mode == "OFF":
        print("❌ MARKET OFF")
        return

    # ===== SECTOR =====
    sector_df = sector_money_flow(df_symbols)
    sector_df = sector_rotation(sector_df)

    top_sectors = sector_df.head(3)

    print("\n🔥 TOP SECTORS:")
    for _, row in top_sectors.iterrows():
        print(f"{row['sector']} | score={round(row['rotation_score'],2)}")

    # ===== LEADERS =====
    leaders = []

    for _, row in top_sectors.iterrows():
        stocks = pick_leaders(df_symbols, row["sector"])
        for _, s in stocks.iterrows():
            leaders.append(s["symbol"])

    leaders = list(set(leaders))
    print("\n🔥 RAW LEADERS:", leaders)

    # ===== FILTER =====
    df_index = load_index()
    scored = []

    for symbol in leaders:
        try:
            df = load_stock_data(symbol)

            rs = relative_strength(df, df_index)
            voe = voe_score(df, df_index)
            inst = institutional_score(df)
            mf = money_flow_score(df)
            acc = detect_accumulation(df)
            flow_acc = flow_timeline(df)

            # 🔥 dynamic RS theo MODE + SESSION
            if mode == "SAFE":
                rs_cond = rs > -0.02
            elif session == "MORNING":
                rs_cond = rs > -0.05
            else:
                rs_cond = rs > -0.08

            if rs_cond:

                score = (
                    rs * 2 +
                    voe * 1.5 +
                    inst * 1.5 +
                    mf * 1.2 +
                    (1 if acc else 0)
                )

                # 🔥 boost dòng tiền tích lũy nhiều ngày
                score += flow_acc * 1.2

                # 🔥 session boost
                if session == "MORNING":
                    score *= 1.1
                elif session == "CLOSE":
                    score *= 1.2

                scored.append((symbol, score))

        except Exception as e:
            print(symbol, "FILTER ERROR:", str(e))

    scored = sorted(scored, key=lambda x: x[1], reverse=True)

    # fallback
    if not scored:
        leaders = leaders[:10]
    else:
        if mode == "SAFE":
            leaders = [s[0] for s in scored[:8]]
        else:
            leaders = [s[0] for s in scored[:15]]

    print("\n🔥 STRONG LEADERS:", leaders)

    # ===== ENTRY =====
    print("\nSCAN ENTRY...\n")

    signals = []

    for symbol in leaders:

        try:
            df = load_stock_data(symbol)
            price = df["close"].iloc[-1]

            ok, f = validate_entry(df)

            print(f"{symbol} | price={round(price,2)} | type={f['type'] if f else None}")

            if ok:

                # 🔥 tránh mua đuổi (AGGRESSIVE)
                if mode == "AGGRESSIVE":
                    if abs(price - f["entry"]) / f["entry"] > 0.08:
                        print("   ❌ too far")
                        continue

                rr = (f["tp1"] - f["entry"]) / (f["entry"] - f["sl"])

                # 🔥 loại RR quá thấp
                if rr < 1.2:
                    print("   ❌ low RR")
                    continue

                score = rr

                # 🔥 ưu tiên loại tín hiệu
                if f["type"] == "PRE":
                    score *= 1.6
                elif f["type"] == "EARLY":
                    score *= 1.3
                elif f["type"] == "STRONG":
                    score *= 1.0

                # 🔥 session boost
                if session == "CLOSE":
                    score *= 1.2

                if mode == "AGGRESSIVE":
                    score *= 1.2

                signals.append({
                    "symbol": symbol,
                    "entry": f["entry"],
                    "sl": f["sl"],
                    "tp1": f["tp1"],
                    "tp2": f["tp2"],
                    "rr": rr,
                    "type": f["type"],
                    "score": score
                })

                log_trade(symbol, f["entry"], f["sl"], f["tp1"])

                print("   ✅ SIGNAL")

            else:
                print("   ❌ skip")

        except Exception as e:
            print(symbol, "ERROR:", str(e))

    signals = sorted(signals, key=lambda x: x["score"], reverse=True)

    print("\nTOTAL SIGNAL:", len(signals))

    # ===== TELEGRAM =====
    if signals:

        msg = f"🔥 SMART MONEY SIGNALS ({session})\n\n"

        for s in signals:
            msg += (
                f"{s['symbol']} ({s['type']})\n"
                f"Entry: {round(s['entry'],2)}\n"
                f"SL: {round(s['sl'],2)}\n"
                f"TP1: {round(s['tp1'],2)}\n"
                f"TP2: {round(s['tp2'],2)}\n"
                f"RR: {round(s['rr'],2)}\n\n"
            )

        send_telegram(msg)

    else:
        print("⚠️ NO SIGNAL")


if __name__ == "__main__":
    main()
