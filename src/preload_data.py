import pandas as pd
import os
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from data_loader import load_stock_data, fetch_with_source
from symbol_loader import load_symbols

SAVE_DIR = "data/market"
os.makedirs(SAVE_DIR, exist_ok=True)

MAX_WORKERS = 5   # 🔥 chỉnh 3–6 tùy tốc độ


def fetch_incremental(symbol, start, end):

    for src in ["VCI", "MSN", "KBS"]:
        try:
            df = fetch_with_source(symbol, src, start, end)
            if df is not None and not df.empty:
                return df
        except:
            continue
    return None


def normalize(df):

    return df.rename(columns={
        "time": "date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume"
    })


def update_symbol(symbol):

    path = f"{SAVE_DIR}/{symbol}.csv"

    try:
        if not os.path.exists(path):
            print("🆕 FULL LOAD:", symbol)
            df = load_stock_data(symbol)
            return symbol, df

        df_old = pd.read_csv(path)

        if df_old.empty or "date" not in df_old.columns:
            print("⚠️ CORRUPT:", symbol)
            df = load_stock_data(symbol)
            return symbol, df

        last_date = df_old["date"].iloc[-1]

        start = pd.to_datetime(last_date) + pd.Timedelta(days=1)
        end = datetime.date.today()

        if start.date() > end:
            return symbol, df_old

        new_df = fetch_incremental(symbol, start, end)

        if new_df is None or new_df.empty:
            return symbol, df_old

        new_df = normalize(new_df)

        df = pd.concat([df_old, new_df])
        df = df.drop_duplicates(subset=["date"])
        df = df.sort_values("date")

        print("🔄", symbol)

        return symbol, df

    except Exception as e:
        print("❌ ERROR:", symbol)
        return symbol, None


def main():

    df_symbols = load_symbols()
    symbols = df_symbols["symbol"].tolist()

    print("🚀 PRELOAD PARALLEL:", len(symbols))

    success = 0
    fail = 0

    # 🔥 MULTI THREAD
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = [executor.submit(update_symbol, s) for s in symbols]

        for future in as_completed(futures):

            symbol, df = future.result()

            if df is not None:
                df.to_csv(f"{SAVE_DIR}/{symbol}.csv", index=False)
                success += 1
            else:
                fail += 1

    print("\n===== RESULT =====")
    print("✅ SUCCESS:", success)
    print("❌ FAIL:", fail)


if __name__ == "__main__":
    main()
