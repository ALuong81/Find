import pandas as pd
import os
from data_loader import load_stock_data
from symbol_loader import load_symbols

SAVE_DIR = "data/market"
os.makedirs(SAVE_DIR, exist_ok=True)

def update_symbol(symbol):

    path = f"{SAVE_DIR}/{symbol}.csv"

    # nếu chưa có file → load full
    if not os.path.exists(path):
        print("FULL LOAD:", symbol)
        return None

    df_old = pd.read_csv(path)

    last_date = df_old["date"].iloc[-1]

    import datetime
    start = pd.to_datetime(last_date) + pd.Timedelta(days=1)
    end = datetime.date.today()

    # 🔥 chỉ load phần thiếu
    new_df = fetch_with_source(symbol, "VCI", start, end)

    if new_df is None or new_df.empty:
        return df_old

    df = pd.concat([df_old, new_df])
    df = df.drop_duplicates(subset=["date"])

    return df
    

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
