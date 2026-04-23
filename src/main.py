from symbol_loader import load_symbols
from data_loader import load_stock_data, load_index

from market_ranking import market_ranking
from entry import validate_entry
from tracker import log_trade

import os
import requests


def send_telegram(msg):

    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": chat_id,
            "text": msg
        })
    except:
        pass


def main():

    print("🚀 START BOT")

    df_symbols = load_symbols()

    print("TOTAL SYMBOLS:", len(df_symbols))

    # 🔥 1. RANK THỊ TRƯỜNG
    market = market_ranking(df_symbols, load_stock_data)

    print("RANKED:", len(market))

    # 🔥 2. FILTER CỔ MẠNH THẬT
    market = [m for m in market if m["score"] > 0.1]

    # 🔥 sort lại cho chắc
    market = sorted(market, key=lambda x: x["score"], reverse=True)

    print("AFTER FILTER:", len(market))

    # 🔥 lấy top
    top_stocks = market[:10]

    print("TOP PICKS:", [m["symbol"] for m in top_stocks])

    print("SCAN ENTRY...\n")

    signals = []

    # 🔥 3. SCAN ENTRY
    for item in top_stocks:

        symbol = item["symbol"]
        score = round(item["score"], 3)

        try:
            df = load_stock_data(symbol)

            ok, f = validate_entry(df)

            last_price = df["close"].iloc[-1]

            print(f"{symbol} | price={round(last_price,2)} | score={score}")

            if ok:
                signals.append({
                    "symbol": symbol,
                    "entry": f["entry"],
                    "sl": f["sl"],
                    "tp1": f["tp1"],
                    "tp2": f["tp2"],
                    "score": score
                })

                log_trade(symbol, f["entry"], f["sl"], f["tp1"])

                print(f"   ✅ SIGNAL")

            else:
                print(f"   ❌ skip")

        except Exception as e:
            print(f"{symbol} ERROR")
            continue

    print("\nTOTAL SIGNAL:", len(signals))

    # 🔥 4. SORT SIGNAL MẠNH NHẤT
    signals = sorted(signals, key=lambda x: x["score"], reverse=True)

    # 🔥 5. TELEGRAM OUTPUT
    if signals:

        msg = "🔥 TOP SIGNALS:\n\n"

        for s in signals:

            msg += (
                f"{s['symbol']} (score {s['score']})\n"
                f"Entry: {round(s['entry'],2)}\n"
                f"SL: {round(s['sl'],2)}\n"
                f"TP1: {round(s['tp1'],2)}\n"
                f"TP2: {round(s['tp2'],2)}\n\n"
            )

        print("\nSEND TELEGRAM...")
        send_telegram(msg)

    else:
        print("⚠️ NO SIGNAL TODAY")


if __name__ == "__main__":
    main()
