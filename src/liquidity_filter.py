import pandas as pd
import os
from data_loader import load_stock_data

CACHE_FILE = "data/liquidity.csv"


# =========================
# 🔥 CORE METRICS
# =========================

def calculate_liquidity(df):
    """
    Thanh khoản = giá trị giao dịch trung bình 20 ngày
    """
    vol = df["volume"].tail(20).mean()
    price = df["close"].iloc[-1]
    return vol * price


def calculate_momentum(df):
    """
    Momentum = % tăng giá 20 ngày
    """
    if len(df) < 20:
        return 0
    return (df["close"].iloc[-1] / df["close"].iloc[-20]) - 1


def calculate_volume_score(df):
    """
    Volume spike = volume hiện tại so với trung bình
    """
    vol_now = df["volume"].iloc[-1]
    vol_avg = df["volume"].tail(20).mean()

    if vol_avg == 0:
        return 0

    return vol_now / vol_avg


def calculate_trend_score(df):
    """
    Trend = MA20 vs MA50
    """
    if len(df) < 50:
        return 0

    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]

    return 1 if ma20 > ma50 else -1


# =========================
# 🔥 SMART MONEY FLOW SCORE
# =========================

def calculate_smart_score(df):

    try:
        liquidity = calculate_liquidity(df)
        momentum = calculate_momentum(df)
        volume_score = calculate_volume_score(df)
        trend = calculate_trend_score(df)

        # 🔥 normalize nhẹ
        score = (
            (momentum * 2) +
            (volume_score * 0.5) +
            (trend * 1)
        )

        return liquidity, score

    except:
        return 0, 0


# =========================
# 🔥 MAIN RANKING
# =========================

def rank_liquidity(df_symbols, top_n=50, use_cache=True):

    # 🔥 load cache nếu có
    if use_cache and os.path.exists(CACHE_FILE):

        print("⚡ LOAD LIQUIDITY CACHE")

        df = pd.read_csv(CACHE_FILE)

        df = df.sort_values("score", ascending=False)

        return df.head(top_n)

    print("🚀 CALCULATE LIQUIDITY + MONEY FLOW...")

    results = []

    for _, row in df_symbols.iterrows():

        symbol = row["symbol"]

        try:
            df = load_stock_data(symbol)

            liquidity, score = calculate_smart_score(df)

            results.append({
                "symbol": symbol,
                "liquidity": liquidity,
                "score": score
            })

            print(f"{symbol} | liq={round(liquidity/1e9,2)}B | score={round(score,2)}")

        except:
            continue

    df = pd.DataFrame(results)

    # 🔥 lọc cổ có thanh khoản tối thiểu
    df = df[df["liquidity"] > 1e9]   # > 1 tỷ / ngày

    # 🔥 sort theo smart money flow
    df = df.sort_values(["score", "liquidity"], ascending=False)

    # 🔥 save cache
    os.makedirs("data", exist_ok=True)
    df.to_csv(CACHE_FILE, index=False)

    return df.head(top_n)
