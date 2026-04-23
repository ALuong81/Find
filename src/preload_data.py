import pandas as pd
from data_loader import load_stock_data
from symbol_loader import load_symbols
import os

SAVE_DIR = "data/market"
os.makedirs(SAVE_DIR, exist_ok=True)


def main():

    df_symbols = load_symbols()

    print("🚀 PRELOAD DATA:", len(df_symbols))

    for _, row in df_symbols.iterrows():

        symbol = row["symbol"]

        try:
            df = load_stock_data(symbol)

            df.to_csv(f"{SAVE_DIR}/{symbol}.csv", index=False)

            print("✅", symbol)

        except Exception as e:
            print("❌", symbol)

    print("DONE PRELOAD")


if __name__ == "__main__":
    main()
