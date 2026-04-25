re import pandas as pd
import os
from data_loader import load_stock_data

CACHE_FILE = "data/liquidity.csv"


# =========================
# 🔥 CORE METRICS (GIỮ NGUYÊN)
# =========================

def calculate_liquidity(df):
    vol = df["volume"].tail(20).mean()
    price = df["close"].iloc[-1]
    return vol * price


def calculate_momentum(df):
    if len(df) < 20:
        return 0
    return (df["close"].iloc[-1] / df["close"].iloc[-20]) - 1


def calculate_volume_score(df):
    vol_now = df["volume"].iloc[-1]
    vol_avg = df["volume"].tail(20).mean()

    if vol_avg == 0:
        return 0

    return vol_now / vol_avg


def calculate_trend_score(df):
    if len(df) < 50:
        return 0

    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]

    return 1 if ma20 > ma50 else -1


# =========================
# 🔥 SMART SCORE (GIỮ NGUYÊN)
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

    except:
        return 0, 0


# =========================
# 🔥 MAIN (FIX KIẾN TRÚC)
# =========================

def rank_liquidity(df_symbols, top_n=50, use_cache=True, min_liquidity=5e8):
    """
    min_liquidity mặc định 0.5 tỷ (giảm từ 1 tỷ để tránh empty)
    """

    # =========================
    # 🔥 LOAD CACHE (SAFE)
    # =========================
    if use_cache and os.path.exists(CACHE_FILE):
        try:
            print("⚡ LOAD LIQUIDITY CACHE")

            df = pd.read_csv(CACHE_FILE)

            # 🔥 đảm bảo cột tồn tại
            if "symbol" in df.columns and "liquidity" in df.columns:
                df = df.sort_values(["liquidity", "score"], ascending=False)
                return df.head(top_n)

        except:
            print("⚠️ CACHE ERROR → RECALCULATE")

    # =========================
    # 🔥 CALCULATE
    # =========================
    print("🚀 CALCULATE LIQUIDITY + SMART FLOW...")

    results = []

    for _, row in df_symbols.iterrows():

        symbol = row["symbol"]

        try:
            df = load_stock_data(symbol)

            if df is None or df.empty or len(df) < 20:
                continue

            # 🔥 FIX DATETIME (QUAN TRỌNG)
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])

            liquidity, score = calculate_smart_score(df)

            if liquidity <= 0:
                continue

            results.append({
                "symbol": symbol,
                "liquidity": liquidity,
                "score": score
            })

            print(f"{symbol} | liq={round(liquidity/1e9,2)}B | score={round(score,2)}")

        except:
            continue

    df = pd.DataFrame(results)

    # =========================
    # 🔥 FALLBACK (QUAN TRỌNG)
    # =========================
    if df.empty:
        print("⚠️ NO DATA → fallback ALL SYMBOLS")
        return df_symbols.copy()

    # =========================
    # 🔥 LIQUIDITY FILTER (MỀM HƠN)
    # =========================
    df = df[df["liquidity"] > min_liquidity]

    if df.empty:
        print("⚠️ LIQUIDITY FILTER EMPTY → fallback NO FILTER")
        df = pd.DataFrame(results)

    # =========================
    # 🔥 SORT (LIQUIDITY FIRST)
    # =========================
    df = df.sort_values(["liquidity", "score"], ascending=False)

    # =========================
    # 🔥 SAVE CACHE
    # =========================
    try:
        os.makedirs("data", exist_ok=True)
        df.to_csv(CACHE_FILE, index=False)
    except:
        pass

    return df.head(top_n)
