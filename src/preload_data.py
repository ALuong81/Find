import pandas as pd
import os
from data_loader import load_stock_data
from symbol_loader import load_symbols

SAVE_DIR = "data/market"
os.makedirs(SAVE_DIR, exist_ok=True)

def main():

    df_symbols = load_symbols()

    for _, row in df_symbols.iterrows():
        symbol = row["symbol"]

        try:
            df = load_stock_data(symbol)
            df.to_csv(f"{SAVE_DIR}/{symbol}.csv", index=False)
            print("OK", symbol)
        except:
            print("FAIL", symbol)

if __name__ == "__main__":
    main()
