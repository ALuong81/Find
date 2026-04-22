import logging
logging.getLogger("vnstock").setLevel(logging.CRITICAL)

from symbol_loader import load_symbols
from data_loader import load_stock_data, load_index

from market_ranking import market_ranking
from sector_ranking import sector_ranking

from fake_breakout import detect_fake_breakout
from entry import validate_entry
from risk import market_risk

from alert import send


def main():

    print("🚀 START BOT")

    # 1. load symbols
    df_symbols = load_symbols()
    print("TOTAL SYMBOLS:", len(df_symbols))

    if df_symbols.empty:
        print("❌ NO SYMBOLS")
        return

    # 2. ranking
    market = market_ranking(df_symbols, load_stock_data)
    print("RANKED:", len(market))

    if not market:
        print("❌ NO MARKET DATA")
        return

    top_stocks = market[:20]
    top_sectors = sector_ranking(market)[:5]

    print("TOP SECTORS:", top_sectors)

    # 3. risk check
    df_index = load_index()
    risk = market_risk(df_index)

    print("RISK:", risk)

    if risk >= 3:
        send("🚨 MARKET RISK HIGH - STOP")
        print("STOP DUE TO RISK")
        return

    # 4. ALWAYS SEND OVERVIEW (quan trọng)
    msg = "📊 BOT RUNNING\n\n"

    msg += "🔥 SECTORS:\n"
    for s, sc in top_sectors:
        msg += f"{s}: {round(sc,3)}\n"

    msg += "\n💪 TOP STOCKS:\n"
    for s in top_stocks[:10]:
        msg += f"{s['symbol']} {round(s['score'],3)}\n"

    send(msg)

    print("SCAN ENTRY...")

    count = 0

    # 5. scan entry
    for item in top_stocks:

        symbol = item["symbol"]

        try:
            df = load_stock_data(symbol)

            if detect_fake_breakout(df):
                print(symbol, "❌ fake breakout")
                continue

            ok, fibo = validate_entry(df)

            if ok:
                count += 1

                print(symbol, "✅ SIGNAL")

                send(f"""
📈 {symbol}

Entry: {round(fibo["entry"],2)}
SL: {round(fibo["sl"],2)}
TP1: {round(fibo["tp1"],2)}
TP2: {round(fibo["tp2"],2)}
""")

        except Exception as e:
            print(symbol, "ERROR:", e)
            continue

    print("TOTAL SIGNAL:", count)


if __name__ == "__main__":
    main()
