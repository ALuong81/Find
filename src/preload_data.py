import pandas as pd
import os
import datetime

from data_loader import load_stock_data, fetch_with_source
from symbol_loader import load_symbols

SAVE_DIR = "data/market"
os.makedirs(SAVE_DIR, exist_ok=True)


def fetch_incremental(symbol, start, end):
    """
    🔥 thử nhiều source để tránh lỗi API
    """
    for src in ["VCI", "MSN", "KBS"]:
        try:
            df = fetch_with_source(symbol, src, start, end)
            if df is not None and not df.empty:
                return df
        except:
            continue
    return None


def normalize(df):
    """
    🔥 chuẩn hóa format dataframe
    """
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

    # 🔥 chưa có file → load full
    if not os.path.exists(path):
        print("🆕 FULL LOAD:", symbol)
        df = load_stock_data(symbol)
        return df

    try:
        df_old = pd.read_csv(path)

        if df_old.empty or "date" not in df_old.columns:
            print("⚠️ CORRUPT FILE → RELOAD:", symbol)
            return load_stock_data(symbol)

        last_date = df_old["date"].iloc[-1]

        start = pd.to_datetime(last_date) + pd.Timedelta(days=1)
        end = datetime.date.today()

        # 🔥 không có gì để update
        if start.date() > end:
            print("⏭ SKIP (UP-TO-DATE):", symbol)
            return df_old

        new_df = fetch_incremental(symbol, start, end)

        if new_df is None or new_df.empty:
            print("⚠️ NO NEW DATA:", symbol)
            return df_old

        new_df = normalize(new_df)

        df = pd.concat([df_old, new_df])
        df = df.drop_duplicates(subset=["date"])
        df = df.sort_values("date")

        print("🔄 UPDATED:", symbol)

        return df

    except Exception as e:
        print("❌ ERROR:", symbol)
        return None


def main():

    df_symbols = load_symbols()

    print("🚀 PRELOAD START")
    print("TOTAL SYMBOLS:", len(df_symbols))

    success = 0
    fail = 0

    for _, row in df_symbols.iterrows():

        symbol = row["symbol"]

        try:
            df = update_symbol(symbol)

            if df is not None:
                df.to_csv(f"{SAVE_DIR}/{symbol}.csv", index=False)
                success += 1
            else:
                fail += 1

        except:
            fail += 1
            print("❌ FAIL:", symbol)

    print("\n===== RESULT =====")
    print("✅ SUCCESS:", success)
    print("❌ FAIL:", fail)
    print("DONE PRELOAD")


if __name__ == "__main__":
    main()
