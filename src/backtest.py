import pandas as pd
import numpy as np

from data_loader import load_stock_data, load_index
from symbol_loader import load_symbols

from smart_money import sector_money_flow, pick_leaders
from sector_rotation import sector_rotation
from relative_strength import relative_strength
from voe import voe_score
from accumulation import detect_accumulation
from institutional import institutional_score
from institutional_flow import institutional_flow_score
from money_flow import money_flow_score
from flow_timeline import flow_timeline

from entry_engine_v7 import entry_score_v7
from meta_filter_v7 import meta_filter_v7, update_meta_v7, save_meta


INITIAL_CAPITAL = 100000
MAX_HOLD_DAYS = 15


DEFAULT_CONFIG = {
    "meta_threshold": 0.55,
    "cooldown_days": 3,
    "max_trades": 2
}


def market_regime(df_index):

    close = df_index["close"]

    ret_5 = close.pct_change(5).iloc[-1]
    ret_20 = close.pct_change(20).iloc[-1]
    vol = close.pct_change().rolling(20).std().iloc[-1]

    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]

    trend = 1 if ma20 > ma50 else -1

    score = ret_5 * 2 + ret_20 * 1.5 - vol * 2 + trend
    score = np.tanh(score * 3)

    if score > 0.3:
        return "AGGRESSIVE", score
    elif score > -0.2:
        return "NEUTRAL", score
    else:
        return "DEFENSIVE", score


def simulate_trade(df, entry, sl, rr):

    tp1 = entry + (entry - sl) * 1.0
    tp2 = entry + (entry - sl) * rr

    hit_tp1 = False

    for i in range(len(df)):
        h = df["high"].iloc[i]
        l = df["low"].iloc[i]

        if l <= sl:
            return -1

        if not hit_tp1 and h >= tp1:
            hit_tp1 = True
            sl = entry

        if h >= tp2:
            return 1

        if i >= 5:
            if not hit_tp1:
                return -0.5

    return 0


def preload_all(symbols):

    data_map = {}

    for symbol in symbols:
        try:
            df = load_stock_data(symbol)

            if df is None or df.empty:
                continue

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])
            df = df.sort_values("date")

            data_map[symbol] = df

        except:
            continue

    return data_map


def run_backtest(config=None, start_date="2023-01-01"):

    if config is None:
        config = DEFAULT_CONFIG

    start_date = pd.to_datetime(start_date)

    df_symbols = load_symbols()
    df_index_full = load_index()

    df_index_full["date"] = pd.to_datetime(df_index_full["date"], errors="coerce")
    df_index_full = df_index_full.sort_values("date")

    equity = INITIAL_CAPITAL
    history = []
    last_trade = {}

    unique_dates = sorted(df_index_full["date"].unique())
    data_map = preload_all(df_symbols["symbol"].tolist())

    for date in unique_dates:

        if date < start_date:
            continue

        df_index = df_index_full[df_index_full["date"] <= date]

        if len(df_index) < 50:
            continue

        mode, _ = market_regime(df_index)

        if mode == "DEFENSIVE":
            continue

        if df_index["close"].iloc[-1] < df_index["close"].iloc[-5]:
            continue

        base_risk_pct = 0.02
        max_trades = config["max_trades"]

        sector_df = sector_money_flow(df_symbols)
        sector_df = sector_rotation(sector_df)

        leaders = []
        for _, row in sector_df.head(5).iterrows():
            leaders += pick_leaders(df_symbols, row["sector"])["symbol"].tolist()

        leaders = list(set(leaders))

        scored = []

        for symbol in leaders:

            if symbol not in data_map:
                continue

            df_full = data_map[symbol]
            df = df_full[df_full["date"] <= date]

            if len(df) < 50:
                continue

            try:
                rs = relative_strength(df, df_index)
                voe = voe_score(df, df_index)
                inst = institutional_score(df)
                inst_flow = institutional_flow_score(df)
                mf = money_flow_score(df)
                flow_acc = flow_timeline(df)
                acc = detect_accumulation(df)

                score = (
                    rs * 2 +
                    voe * 1.5 +
                    inst * 1.2 +
                    inst_flow * 1.8 +
                    mf * 1.3 +
                    flow_acc * 1.2 +
                    (1 if acc else 0)
                )

                scored.append((symbol, score, rs))

            except:
                continue

        scored = sorted(scored, key=lambda x: x[1], reverse=True)[:5]

        trades_today = 0

        for symbol, total_score, rs in scored:

            if trades_today >= max_trades:
                break

            if symbol in last_trade:
                if (date - last_trade[symbol]).days < config["cooldown_days"]:
                    continue

            df_full = data_map[symbol]
            df = df_full[df_full["date"] <= date]

            f = entry_score_v7(df)
            if f is None:
                print(symbol, "⛔ entry_fail")
                continue

            range_10 = (df["high"].tail(10).max() - df["low"].tail(10).min()) / df["low"].tail(10).min()
            if range_10 < 0.02:
                continue

            if df["close"].iloc[-1] < df["close"].iloc[-3]:
                continue
            if df["close"].iloc[-1] < df["open"].iloc[-1]:
                continue

            print(symbol, f["type"], round(f["score"], 2))

            risk = f["entry"] - f["sl"]
            if risk <= 0:
                continue

            rr = 1.6 + min(0.6, f["score"] * 0.02)

            signal = {
                "symbol": symbol,
                "rr": rr,
                "score": f["score"],
                "regime": mode,
                "correlation": rs,
                "volatility": f["volatility"],
                "liquidity": f["liquidity"],
                "type": f["type"],

                "trend_strength": abs(
                    df["close"].rolling(20).mean().iloc[-1] -
                    df["close"].rolling(50).mean().iloc[-1]
                ) / (df["close"].rolling(50).mean().iloc[-1] + 1e-9),

                "vol_ratio": df["volume"].iloc[-1] / (
                    df["volume"].rolling(20).mean().iloc[-1] + 1e-9
                ),

                "breakout_strength": (
                    df["close"].iloc[-1] -
                    df["high"].tail(20).max()
                ) / (df["high"].tail(20).max() + 1e-9)
            }

            prob = meta_filter_v7(signal)

            if prob < 0.55 and len(history) > 100:
                continue

            size_scale = 0.2 + prob * 0.5

            future_df = df_full[df_full["date"] > date].head(MAX_HOLD_DAYS)
            if future_df.empty:
                continue

            result = simulate_trade(future_df, f["entry"], f["sl"], rr)

            update_meta_v7(signal, result)

            risk_amount = equity * base_risk_pct * size_scale

            if result == 1:
                equity += risk_amount * rr
            elif result == -1:
                equity -= risk_amount
            elif result == -0.5:
                equity -= risk_amount * 0.5

            history.append({
                "date": date,
                "symbol": symbol,
                "result": result,
                "equity": equity,
                "rr": rr,
                "meta_prob": prob
            })

            last_trade[symbol] = date
            trades_today += 1

    save_meta()

    return pd.DataFrame(history)
