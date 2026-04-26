import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from data_loader import load_stock_data, fetch_with_source
from symbol_loader import load_symbols
from liquidity_filter import rank_liquidity

SAVE_DIR = "data/market"
BLACKLIST_FILE = "data/blacklist.txt"

os.makedirs(SAVE_DIR, exist_ok=True)

MAX_WORKERS = 5
MAX_RETRY = 3


# =========================
# 🔥 BLACKLIST
# =========================
def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return set()
    try:
        with open(BLACKLIST_FILE, "r") as f:
            return set(x.strip() for x in f.readlines())
    except:
        return set()


def save_blacklist(blacklist):
    try:
        with open(BLACKLIST_FILE, "w") as f:
            for s in blacklist:
                f.write(s + "\n")
    except:
        pass


# =========================
# FETCH INCREMENTAL (RETRY)
# =========================
def fetch_incremental(symbol, start, end):

    for attempt in range(MAX_RETRY):

        for src in ["VCI", "MSN", "KBS"]:
            try:
                df = fetch_with_source(symbol, src, start, end)

                if df is not None and not df.empty:
                    return df

            except Exception:
                continue

        time.sleep(0.5)  # 🔥 backoff nhẹ

    return None


# =========================
# NORMALIZE
# =========================
def normalize(df):

    required_cols = ["time", "open", "high", "low", "close", "volume"]

    if df is None or df.empty:
        return None

    if not all(col in df.columns for col in required_cols):
        return None

    try:
        df = df.rename(columns={"time": "date"})

        df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
        df["date"] = df["date"].dt.tz_convert(None)
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

        df = df.dropna(subset=["date"])

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["close", "volume"])

        df = df.sort_values("date")
        df = df.drop_duplicates(subset=["date"], keep="last")

        return df

    except Exception:
        return None


# =========================
# CLEAN OLD
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
# UPDATE 1 SYMBOL (RETRY + SKIP)
# =========================
def update_symbol(symbol, blacklist):

    if symbol in blacklist:
        print("🚫 SKIP BLACKLIST:", symbol)
        return symbol, None, True

    path = f"{SAVE_DIR}/{symbol}.csv"

    for attempt in range(MAX_RETRY):

        try:
            # =========================
            # FULL LOAD
            # =========================
            if not os.path.exists(path):
                print("🆕 FULL LOAD:", symbol)

                df = normalize(load_stock_data(symbol))

                if df is not None:
                    return symbol, df, False

            # =========================
            # LOAD OLD
            # =========================
            try:
                df_old = pd.read_csv(path)
            except:
                continue

            df_old = clean_old(df_old)

            if df_old is None or df_old.empty:
                df = normalize(load_stock_data(symbol))
                return symbol, df, False

            last_date = pd.to_datetime(df_old["date"].max(), errors="coerce")

            start = last_date + pd.Timedelta(days=1)
            end = pd.Timestamp.today().normalize()

            if start > end:
                return symbol, df_old, False

            new_df = fetch_incremental(symbol, start, end)
            new_df = normalize(new_df)

            if new_df is None or new_df.empty:
                return symbol, df_old, False

            df = pd.concat([df_old, new_df], ignore_index=True)

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])

            df = df.sort_values("date")
            df = df.drop_duplicates(subset=["date"], keep="last")

            print(f"🔄 UPDATE: {symbol} (+{len(new_df)})")

            return symbol, df, False

        except Exception as e:
            print(f"⚠️ RETRY {attempt+1}/{MAX_RETRY}:", symbol, str(e))
            time.sleep(0.5)

    # =========================
    # FAIL → BLACKLIST
    # =========================
    print("🚫 ADD BLACKLIST:", symbol)
    return symbol, None, True


# =========================
# MAIN
# =========================
def main():

    df_symbols = load_symbols()
    blacklist = load_blacklist()

    print("CALCULATE LIQUIDITY...")

    df_top = rank_liquidity(df_symbols, top_n=50)

    if df_top is None or df_top.empty or "symbol" not in df_top.columns:
        symbols = df_symbols["symbol"].tolist()
    else:
        symbols = df_top["symbol"].dropna().tolist()

    if not symbols:
        symbols = df_symbols["symbol"].tolist()

    print("🔥 TOP LIQUIDITY:", symbols[:10])
    print("🚀 PRELOAD PARALLEL:", len(symbols))

    success = 0
    fail = 0

    new_blacklist = set(blacklist)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = {
            executor.submit(update_symbol, s, blacklist): s for s in symbols
        }

        for future in as_completed(futures):

            symbol = futures[future]

            try:
                symbol, df, is_bad = future.result()

                if is_bad:
                    new_blacklist.add(symbol)
                    fail += 1
                    continue

                if df is not None and not df.empty:
                    df.to_csv(f"{SAVE_DIR}/{symbol}.csv", index=False)
                    success += 1
                else:
                    print("⚠️ SKIP EMPTY:", symbol)
                    fail += 1

            except Exception as e:
                print("❌ FUTURE ERROR:", symbol, str(e))
                new_blacklist.add(symbol)
                fail += 1

    # =========================
    # SAVE BLACKLIST
    # =========================
    save_blacklist(new_blacklist)

    print("\n===== RESULT =====")
    print("✅ SUCCESS:", success)
    print("❌ FAIL:", fail)
    print("🚫 BLACKLIST SIZE:", len(new_blacklist))


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()
