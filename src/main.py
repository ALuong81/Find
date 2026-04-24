from symbol_loader import load_symbols
from data_loader import load_stock_data, load_index

from smart_money import (
    market_score,
    sector_money_flow,
    pick_leaders
)

from sector_rotation import sector_rotation
from relative_strength import relative_strength
from breakout import breakout_type
from entry import validate_entry
from voe import voe_score
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

    # MARKET
    m = market_score()
    print("MARKET SCORE:", m)

    if m < 0:
        print("❌ MARKET BAD")
        return

    # SECTOR
    sector_df = sector_money_flow(df_symbols)
    sector_df = sector_rotation(sector_df)

    top_sectors = sector_df.head(3)

    print("\n🔥 TOP SECTORS:")
    for _, row in top_sectors.iterrows():
        print(f"{row['sector']} | score={round(row['rotation_score'],2)}")

    # LEADERS
    leaders = []

    for _, row in top_sectors.iterrows():
        stocks = pick_leaders(df_symbols, row["sector"])
        for _, s in stocks.iterrows():
            leaders.append(s["symbol"])

    leaders = list(set(leaders))

    print("\n🔥 RAW LEADERS:", leaders)

    # RS + VOE FILTER
    df_index = load_index()

    scored = []

    for symbol in leaders:
        df = load_stock_data(symbol)
        rs = relative_strength(df, df_index)

        if rs > -0.02:
            score = voe_score(df, df_index)
            scored.append((symbol, score))

    scored = sorted(scored, key=lambda x: x[1], reverse=True)
    leaders = [s[0] for s in scored[:5]]

    print("\n🔥 STRONG LEADERS:", leaders)

    # ENTRY
    print("\nSCAN ENTRY...\n")

    signals = []

    for symbol in leaders:

        try:
            df = load_stock_data(symbol)
            price = df["close"].iloc[-1]

            b_type = breakout_type(df)
            rs = relative_strength(df, df_index)

            if b_type is None:
                continue

            # ❌ loại STRONG yếu
            if b_type == "STRONG":
                vol = df["volume"]
                vol_ma = vol.rolling(20).mean()

                if vol.iloc[-1] < vol_ma.iloc[-1] * 1.5 or rs < 0:
                    print(f"{symbol} | ❌ weak strong")
                    continue

            ok, f = validate_entry(df)

            print(f"{symbol} | price={round(price,2)} | breakout={b_type}")

            if ok:

                rr = (f["tp1"] - f["entry"]) / (f["entry"] - f["sl"])

                score = rr
                if b_type == "EARLY":
                    score *= 1.3

                signals.append({
                    "symbol": symbol,
                    "entry": f["entry"],
                    "sl": f["sl"],
                    "tp1": f["tp1"],
                    "tp2": f["tp2"],
                    "rr": rr,
                    "type": b_type,
                    "score": score
                })

                log_trade(symbol, f["entry"], f["sl"], f["tp1"])

                print("   ✅ SIGNAL")

            else:
                print("   ❌ skip")

        except Exception as e:
            print(f"{symbol} ERROR:", str(e))

    signals = sorted(signals, key=lambda x: x["score"], reverse=True)

    print("\nTOTAL SIGNAL:", len(signals))

    # TELEGRAM
    if signals:

        msg = "🔥 SMART MONEY SIGNALS\n\n"

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
