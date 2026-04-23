from symbol_loader import load_symbols
from data_loader import load_stock_data

from smart_money import (
    market_score,
    sector_money_flow,
    pick_leaders
)

from entry import validate_entry
from tracker import log_trade

import os
import requests


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
    except:
        print("❌ TELEGRAM ERROR")


# =========================
# MAIN
# =========================
def main():

    print("🚀 START BOT")

    df_symbols = load_symbols()

    print("TOTAL SYMBOLS:", len(df_symbols))

    # =========================
    # 1. MARKET FILTER
    # =========================
    m = market_score()

    print("MARKET SCORE:", m)

    if m < 0:
        print("❌ MARKET BAD → STOP")
        send_telegram("❌ Market xấu - dừng giao dịch")
        return

    # =========================
    # 2. SECTOR MONEY FLOW
    # =========================
    sector_df = sector_money_flow(df_symbols)

    if sector_df.empty:
        print("❌ NO SECTOR DATA")
        return

    top_sectors = sector_df.head(3)

    print("\n🔥 TOP SECTORS:")
    for _, row in top_sectors.iterrows():
        print(f"{row['sector']} | score={round(row['score'],2)}")

    # =========================
    # 3. PICK LEADERS
    # =========================
    leaders = []

    for _, row in top_sectors.iterrows():

        sector = row["sector"]

        top_stocks = pick_leaders(df_symbols, sector)

        for _, s in top_stocks.iterrows():
            leaders.append(s["symbol"])

    # remove duplicate
    leaders = list(set(leaders))

    print("\n🔥 LEADERS:", leaders)

    # =========================
    # 4. ENTRY SCAN
    # =========================
    print("\nSCAN ENTRY...\n")

    signals = []

    for symbol in leaders:

        try:
            df = load_stock_data(symbol)

            ok, f = validate_entry(df)

            price = df["close"].iloc[-1]

            print(f"{symbol} | price={round(price,2)}")

            if ok:

                signals.append({
                    "symbol": symbol,
                    "entry": f["entry"],
                    "sl": f["sl"],
                    "tp1": f["tp1"],
                    "tp2": f["tp2"]
                })

                log_trade(symbol, f["entry"], f["sl"], f["tp1"])

                print("   ✅ SIGNAL")

            else:
                print("   ❌ skip")

        except Exception as e:
            print(f"{symbol} ERROR: {str(e)}")
            continue

    print("\nTOTAL SIGNAL:", len(signals))

    # =========================
    # 5. SEND TELEGRAM
    # =========================
    if signals:

        msg = "🔥 SMART MONEY SIGNALS\n\n"

        for s in signals:

            msg += (
                f"{s['symbol']}\n"
                f"Entry: {round(s['entry'],2)}\n"
                f"SL: {round(s['sl'],2)}\n"
                f"TP1: {round(s['tp1'],2)}\n"
                f"TP2: {round(s['tp2'],2)}\n\n"
            )

        print("\n📩 SEND TELEGRAM")
        send_telegram(msg)

    else:
        print("⚠️ NO SIGNAL TODAY")
        send_telegram("⚠️ Không có tín hiệu hôm nay")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()
