from symbol_loader import load_symbols
from data_loader import load_stock_data, load_index

from market_ranking import market_ranking
from sector_ranking import sector_ranking

from fake_breakout import detect_fake_breakout
from entry import validate_entry
from risk import market_risk

from alert import send
from position import position_size

def main():

    print("🚀 START BOT")

    df_symbols = load_symbols()
    print("TOTAL SYMBOLS:", len(df_symbols))

    market = market_ranking(df_symbols, load_stock_data)
    print("RANKED:", len(market))

    if not market:
        return

    # 🔥 chỉ giữ top mạnh
    top_stocks = market[:10]
    top_sectors = sector_ranking(market)[:3]

    print("TOP SECTORS:", top_sectors)

    df_index = load_index()
    risk = market_risk(df_index)

    print("RISK:", risk)

    # luôn gửi overview
    msg = "📊 MARKET\n\n"

    msg += "🔥 SECTORS:\n"
    for s, sc in top_sectors:
        msg += f"{s}: {round(sc,3)}\n"

    msg += "\n💪 TOP STOCKS:\n"
    for s in top_stocks:
        msg += f"{s['symbol']} {round(s['score'],3)}\n"

    send(msg)

    if risk >= 3:
        send("🚨 MARKET RISK HIGH - NO TRADE")
        return

    print("SCAN ENTRY...")

    count = 0

    # 🔥 chỉ lấy top 3
    for item in top_stocks[:5]:

        symbol = item["symbol"]

        try:
            df = load_stock_data(symbol)

            if detect_fake_breakout(df):
                continue

            ok, fibo = validate_entry(df)

            if ok:
                count += 1
                
                size = position_size(100000000, fibo["entry"], fibo["sl"])
                
                send(f"""
📈 {symbol}

Entry: {round(fibo["entry"],2)}
SL: {round(fibo["sl"],2)}
TP1: {round(fibo["tp1"],2)}
TP2: {round(fibo["tp2"],2)}
Size: {size} cp
""")

        except:
            continue

    print("TOTAL SIGNAL:", count)


if __name__ == "__main__":
    main()
