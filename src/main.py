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
    except Exception as e:
        print("❌ TELEGRAM ERROR:", str(e))


# =========================
# MAIN
# =========================
def main():

    print("🚀 START BOT")

    df_symbols = load_symbols()
    print("TOTAL SYMBOLS:", len(df_symbols))

    # =========================
    # 1. MARKET
    # =========================
    m = market_score()
    print("MARKET SCORE:", m)

    if m < 0:
        print("❌ MARKET BAD")
        return

    # =========================
    # 2. SECTOR ROTATION
    # =========================
    sector_df = sector_money_flow(df_symbols)
    sector_df = sector_rotation(sector_df)

    top_sectors = sector_df.head(3)

    print("\n🔥 TOP SECTORS:")
    for _, row in top_sectors.iterrows():
        print(f"{row['sector']} | score={round(row['rotation_score'],2)}")

    # =========================
    # 3. PICK LEADERS
    # =========================
    leaders = []

    for _, row in top_sectors.iterrows():
        sector = row["sector"]
        stocks = pick_leaders(df_symbols, sector)

        for _, s in stocks.iterrows():
            leaders.append(s["symbol"])

    leaders = list(set(leaders))

    print("\n🔥 RAW LEADERS:", leaders)

    # =========================
    # 4. RS FILTER
    # =========================
    df_index = load_index()

    filtered = []

    for symbol in leaders:
        df = load_stock_data(symbol)
        rs = relative_strength(df, df_index)

        if rs > -0.02:
            filtered.append(symbol)

    leaders = filtered

    print("\n🔥 STRONG LEADERS:", leaders)

    # =========================
    # 5. ENTRY
    # =========================
    print("\nSCAN ENTRY...\n")

    signals = []

    for symbol in leaders:

        try:
            df = load_stock_data(symbol)
            price = df["close"].iloc[-1]

            ok, f = validate_entry(df)

            print(f"{symbol} | price={round(price,2)}")

            if ok:

                rr = (f["tp1"] - f["entry"]) / (f["entry"] - f["sl"])

                signals.append({
                    "symbol": symbol,
                    "entry": f["entry"],
                    "sl": f["sl"],
                    "tp1": f["tp1"],
                    "tp2": f["tp2"],
                    "rr": rr
                })

                log_trade(symbol, f["entry"], f["sl"], f["tp1"])

                print("   ✅ SIGNAL")

            else:
                print("   ❌ skip")

        except Exception as e:
            print(f"{symbol} ERROR:", str(e))

    print("\nTOTAL SIGNAL:", len(signals))

    # =========================
    # 6. TELEGRAM
    # =========================
    if signals:

        msg = "🔥 SMART MONEY SIGNALS\n\n"

        for s in signals:
            msg += (
                f"{s['symbol']}\n"
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
