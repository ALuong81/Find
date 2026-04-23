from symbol_loader import load_symbols
from data_loader import load_stock_data, load_index

from market_ranking import market_ranking
from entry import validate_entry
from tracker import log_trade

def main():

    print("🚀 START BOT")

    df_symbols = load_symbols()

    market = market_ranking(df_symbols, load_stock_data)[:10]

    print("SCAN ENTRY...")

    count = 0

    for item in market[:5]:

        symbol = item["symbol"]

        try:
            df = load_stock_data(symbol)

            ok, f = validate_entry(df)

            if ok:
                count += 1

                log_trade(symbol, f["entry"], f["sl"], f["tp1"])

                print(symbol, "✅")

        except:
            continue

    print("TOTAL SIGNAL:", count)

if __name__ == "__main__":
    main()
