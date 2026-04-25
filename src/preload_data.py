import pandas as pd
import os
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from data_loader import load_stock_data, fetch_with_source
from symbol_loader import load_symbols
from liquidity_filter import rank_liquidity

SAVE_DIR = "data/market"
os.makedirs(SAVE_DIR, exist_ok=True)

MAX_WORKERS = 5


# =========================
# FETCH INCREMENTAL
# =========================
def fetch_incremental(symbol, start, end):

    for src in ["VCI", "MSN", "KBS"]:
        try:
            df = fetch_with_source(symbol, src, start, end)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            continue

    return None


# =========================
# NORMALIZE DATA
# =========================
def normalize(df):

    required_cols = ["time", "open", "high", "low", "close", "volume"]

    if not all(col in df.columns for col in required_cols):
        return None

    df = df.rename(columns={
        "time": "date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume"
    })

    df["date"] = pd.to_datetime(df["date"])

    return df


# =========================
# UPDATE 1 SYMBOL
# =========================
def update_symbol(symbol):

    path = f"{SAVE_DIR}/{symbol}.csv"

    try:
        # =========================
        # FULL LOAD
        # =========================
        if not os.path.exists(path):
            print("🆕 FULL LOAD:", symbol)

            df = load_stock_data(symbol)

            if df is not None and not df.empty:
                df["date"] = pd.to_datetime(df["date"])

            return symbol, df

        # =========================
        # LOAD OLD
        # =========================
        df_old = pd.read_csv(path)

        if df_old.empty or "date" not in df_old.columns:
            print("⚠️ CORRUPT:", symbol)
            df = load_stock_data(symbol)
            return symbol, df

        df_old["date"] = pd.to_datetime(df_old["date"])

        last_date = df_old["date"].max()

        start = last_date + pd.Timedelta(days=1)
        end = pd.Timestamp.today().normalize()

        # =========================
        # NO NEED UPDATE
        # =========================
        if start > end:
            print("⏭️ SKIP:", symbol)
            return symbol, df_old

        # =========================
        # FETCH NEW
        # =========================
        new_df = fetch_incremental(symbol, start, end)

        if new_df is None or new_df.empty:
            print("⚠️ NO NEW:", symbol)
            return symbol, df_old

        new_df = normalize(new_df)

        if new_df is None:
            print("❌ BAD FORMAT:", symbol)
            return symbol, df_old

        # =========================
        # MERGE
        # =========================
        df = pd.concat([df_old, new_df])
        df = df.drop_duplicates(subset=["date"])
        df = df.sort_values("date")

        print("🔄 UPDATE:", symbol, f"(+{len(new_df)})")

        return symbol, df

    except Exception as e:
        print("❌ ERROR:", symbol, str(e))
        return symbol, None


# =========================
# MAIN
# =========================
def main():

    df_symbols = load_symbols()

    print("CALCULATE LIQUIDITY...")

    # 🔥 FIX: chỉ là universe filter, KHÔNG phải signal
    df_top = rank_liquidity(df_symbols, top_n=50)

    symbols = df_top["symbol"].tolist()

    print("🔥 TOP LIQUIDITY:", symbols[:10])
    print("🚀 PRELOAD PARALLEL:", len(symbols))

    success = 0
    fail = 0

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


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()
