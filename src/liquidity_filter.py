import pandas as pd
import os
from data_loader import load_stock_data

CACHE_FILE = "data/liquidity.csv"


# =========================
# 🔥 CORE METRICS
# =========================

def calculate_liquidity(df):
    vol = df["volume"].tail(20).mean()
    price = df["close"].iloc[-1]

    if pd.isna(vol) or pd.isna(price):
        return 0

    return vol * price


def calculate_momentum(df):
    if len(df) < 20:
        return 0
    return (df["close"].iloc[-1] / df["close"].iloc[-20]) - 1


def calculate_volume_score(df):
    vol_now = df["volume"].iloc[-1]
    vol_avg = df["volume"].tail(20).mean()

    if vol_avg == 0 or pd.isna(vol_avg):
        return 0

    return vol_now / vol_avg


def calculate_trend_score(df):
    if len(df) < 50:
        return 0

    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]

    if pd.isna(ma20) or pd.isna(ma50):
        return 0

    return 1 if ma20 > ma50 else -1


# =========================
# 🔥 SMART SCORE
# =========================

def calculate_smart_score(df):
    try:
        liquidity = calculate_liquidity(df)
        momentum = calculate_momentum(df)
        volume_score = calculate_volume_score(df)
        trend = calculate_trend_score(df)

        score = (
            (momentum * 2) +
            (volume_score * 0.5) +
            (trend * 1)
        )

        return liquidity, score

    except Exception as e:
        print("SMART SCORE ERROR:", str(e))
        return 0, 0


# =========================
# 🔥 MAIN RANKING (FINAL FIX)
# =========================

def rank_liquidity(df_symbols, top_n=50, use_cache=True, min_liquidity=3e8):
    """
    ✅ FIX FULL:
    - Không phụ thuộc cache 100%
    - Cache chỉ dùng nếu hợp lệ
    - Fallback khi empty
    - Hạ liquidity threshold
    """

    # =========================
    # 🔥 TRY CACHE (SOFT USE)
    # =========================
    cache_df = None

    if use_cache and os.path.exists(CACHE_FILE):
        try:
            print("⚡ TRY LOAD CACHE")

            df_cache = pd.read_csv(CACHE_FILE)

            if {"symbol", "liquidity", "score"}.issubset(df_cache.columns):
                if not df_cache.empty:
                    cache_df = df_cache.sort_values(
                        ["liquidity", "score"],
                        ascending=False
                    )
                    print("✅ CACHE OK")

        except Exception as e:
            print("⚠️ CACHE ERROR:", str(e))

    # =========================
    # 🔥 CALCULATE REAL DATA
    # =========================
    print("🚀 CALCULATE LIQUIDITY...")

    results = []

    for _, row in df_symbols.iterrows():

        symbol = row["symbol"]

        try:
            df = load_stock_data(symbol)

            if df is None or df.empty or len(df) < 20:
                continue

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])

            if df.empty:
                continue

            liquidity, score = calculate_smart_score(df)

            if liquidity <= 0:
                continue

            results.append({
                "symbol": symbol,
                "liquidity": liquidity,
                "score": score
            })

        except Exception as e:
            print("❌ ERROR:", symbol, str(e))
            continue

    df = pd.DataFrame(results)

    # =========================
    # 🔥 HARD FAIL → FALLBACK
    # =========================
    if df.empty:

        print("🔥 NO LIVE DATA → USE CACHE OR FALLBACK")

        if cache_df is not None:
            return cache_df.head(top_n)

        fallback = df_symbols.copy()
        fallback["liquidity"] = 0
        fallback["score"] = 0

        return fallback.head(top_n)

    # =========================
    # 🔥 FILTER (SOFT)
    # =========================
    df_filtered = df[df["liquidity"] > min_liquidity]

    if df_filtered.empty:
        print("⚠️ FILTER TOO STRICT → USE RAW DATA")
        df_filtered = df

    # =========================
    # 🔥 SORT
    # =========================
    df_filtered = df_filtered.sort_values(
        ["liquidity", "score"],
        ascending=False
    )

    # =========================
    # 🔥 SAVE CACHE (NON-BLOCKING)
    # =========================
    try:
        os.makedirs("data", exist_ok=True)
        df_filtered.to_csv(CACHE_FILE, index=False)
    except Exception as e:
        print("⚠️ CACHE SAVE ERROR:", str(e))

    return df_filtered.head(top_n)
