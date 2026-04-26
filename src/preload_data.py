import pandas as pd
import os
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

        except Exception:
            continue

    return None


# =========================
# 🔥 NORMALIZE (FIX TRIỆT ĐỂ TZ)
# =========================
def normalize(df):

    required_cols = ["time", "open", "high", "low", "close", "volume"]

    if df is None or df.empty:
        return None

    if not all(col in df.columns for col in required_cols):
        return None

    try:
        df = df.rename(columns={"time": "date"})

        # 🔥 FIX TZ TRIỆT ĐỂ
        df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
        df["date"] = df["date"].dt.tz_convert(None)
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

        df = df.dropna(subset=["date"])

        # 🔥 ép numeric
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["close", "volume"])

        # 🔥 sort + dedup
        df = df.sort_values("date")
        df = df.drop_duplicates(subset=["date"], keep="last")

        return df

    except Exception:
        return None


# =========================
# 🔥 CLEAN OLD (FIX TZ)
# =========================
def clean_old(df):

    try:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
        df["date"] = df["date"].dt.tz_convert(None)
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

        df = df.dropna(subset=["date"])

        df = df.sort_values("date")
        df = df.drop_duplicates(subset=["date"], keep="last")

        return df

    except Exception:
        return None


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
            df = normalize(df)

            return symbol, df

        # =========================
        # LOAD OLD
        # =========================
        try:
            df_old = pd.read_csv(path)
        except Exception:
            print("⚠️ READ FAIL:", symbol)
            return symbol, None

        df_old = clean_old(df_old)

        if df_old is None or df_old.empty:
            print("⚠️ CORRUPT:", symbol)
            df = normalize(load_stock_data(symbol))
            return symbol, df

        # =========================
        # 🔥 FIX TZ SO SÁNH
        # =========================
        last_date = pd.to_datetime(df_old["date"].max(), errors="coerce")

        start = last_date + pd.Timedelta(days=1)

        # 🔥 FIX CHÍNH: dùng tz-naive
        end = pd.Timestamp.today().normalize()

        # =========================
        # NO UPDATE
        # =========================
        if start > end:
            print("⏭️ SKIP:", symbol)
            return symbol, df_old

        # =========================
        # FETCH NEW
        # =========================
        new_df = fetch_incremental(symbol, start, end)
        new_df = normalize(new_df)

        if new_df is None or new_df.empty:
            print("⚠️ NO NEW:", symbol)
            return symbol, df_old

        # =========================
        # MERGE + CLEAN
        # =========================
        df = pd.concat([df_old, new_df], ignore_index=True)

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        df = df.sort_values("date")
        df = df.drop_duplicates(subset=["date"], keep="last")

        print(f"🔄 UPDATE: {symbol} (+{len(new_df)})")

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

    df_top = rank_liquidity(df_symbols, top_n=50)

    # =========================
    # SAFE SYMBOL LIST
    # =========================
    if df_top is None or df_top.empty or "symbol" not in df_top.columns:
        print("⚠️ LIQUIDITY EMPTY → fallback ALL")
        symbols = df_symbols["symbol"].tolist()
    else:
        symbols = df_top["symbol"].dropna().tolist()

    if not symbols:
        print("⚠️ SYMBOL EMPTY → FORCE ALL")
        symbols = df_symbols["symbol"].tolist()

    print("🔥 TOP LIQUIDITY:", symbols[:10])
    print("🚀 PRELOAD PARALLEL:", len(symbols))

    success = 0
    fail = 0

    # =========================
    # MULTI THREAD
    # =========================
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = {executor.submit(update_symbol, s): s for s in symbols}

        for future in as_completed(futures):

            symbol = futures[future]

            try:
                symbol, df = future.result()

                if df is not None and not df.empty:
                    df.to_csv(f"{SAVE_DIR}/{symbol}.csv", index=False)
                    success += 1
                else:
                    print("⚠️ SKIP EMPTY:", symbol)
                    fail += 1

            except Exception as e:
                print("❌ FUTURE ERROR:", symbol, str(e))
                fail += 1

    print("\n===== RESULT =====")
    print("✅ SUCCESS:", success)
    print("❌ FAIL:", fail)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()
