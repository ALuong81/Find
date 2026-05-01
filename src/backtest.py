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

from entry_engine_v6 import entry_score

from meta_filter_v6 import meta_filter_v6, update_meta_v6
from meta_filter_v2 import save_meta


INITIAL_CAPITAL = 100000
MAX_HOLD_DAYS = 10


# =========================
# RR
# =========================
def calc_rr(entry, sl, tp):
    risk = entry - sl
    reward = tp - entry
    if risk <= 0:
        return 0
    return reward / risk


# =========================
# MARKET REGIME
# =========================
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
    elif score > -0.3:
        return "NEUTRAL", score
    else:
        return "DEFENSIVE", score


# =========================
# SIMULATE
# =========================
def simulate_trade(df, entry, sl, tp):

    for i in range(len(df)):

        h = df["high"].iloc[i]
        l = df["low"].iloc[i]

        if l <= sl and h >= tp:
            return 0

        if l <= sl:
            return -1

        if h >= tp:
            return 1

    return 0


# =========================
# PRELOAD
# =========================
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


# =========================
# BACKTEST
# =========================
# =========================
# BACKTEST
# =========================
def run_backtest(start_date="2023-01-01"):

    start_date = pd.to_datetime(start_date)

    df_symbols = load_symbols()
    df_index_full = load_index()

    df_index_full["date"] = pd.to_datetime(df_index_full["date"], errors="coerce")
    df_index_full = df_index_full.sort_values("date")

    equity = INITIAL_CAPITAL
    peak_equity = equity

    history = []
    last_trade = {}

    unique_dates = sorted(df_index_full["date"].unique())
    data_map = preload_all(df_symbols["symbol"].tolist())

    for date in unique_dates:

        if date < start_date:
            continue

        peak_equity = max(peak_equity, equity)

        df_index = df_index_full[df_index_full["date"] <= date]

        if len(df_index) < 50:
            continue

        mode, m_score = market_regime(df_index)

        if mode == "NEUTRAL" and abs(m_score) < 0.05:
            continue

        if mode == "AGGRESSIVE":
            base_risk_pct = 0.02
            max_trades = 3
            rr_min = 1.1
            tp_mult = 2.5
            meta_th = 0.52
        elif mode == "NEUTRAL":
            base_risk_pct = 0.015
            max_trades = 2
            rr_min = 1.2
            tp_mult = 2.0
            meta_th = 0.55
        else:
            base_risk_pct = 0.01
            max_trades = 1
            rr_min = 1.3
            tp_mult = 1.6
            meta_th = 0.60

        # =========================
        # SECTOR
        # =========================
        sector_df = sector_money_flow(df_symbols)
        sector_df = sector_rotation(sector_df)

        leaders = []
        for _, row in sector_df.head(3).iterrows():
            leaders += pick_leaders(df_symbols, row["sector"])["symbol"].tolist()

        leaders = list(set(leaders))

        # =========================
        # SCORING
        # =========================
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
                    rs * 2 + voe * 1.5 + inst * 1.2 +
                    inst_flow * 1.8 + mf * 1.3 +
                    flow_acc * 1.2 + (1 if acc else 0)
                )

                scored.append((symbol, score, rs))

            except:
                continue

        scored = sorted(scored, key=lambda x: x[1], reverse=True)[:10]

        trades_today = 0

        for symbol, _, rs in scored:

            if trades_today >= max_trades:
                break

            if symbol in last_trade:
                if (date - last_trade[symbol]).days < 5:
                    continue

            df_full = data_map[symbol]
            df = df_full[df_full["date"] <= date]

            # =========================
            # 🔥 TREND FILTER (NEW)
            # =========================
            ma20 = df["close"].rolling(20).mean().iloc[-1]
            ma50 = df["close"].rolling(50).mean().iloc[-1]

            if np.isnan(ma20) or np.isnan(ma50):
                continue

            trend_ok = ma20 > ma50
            if not trend_ok:
                continue

            # =========================
            # ENTRY
            # =========================
            f = entry_score(df)
            if f is None:
                continue

            print(f"{symbol} | score={f['score']:.2f} | vol={f['volatility']:.3f}")

            # VOL FILTER
            if f["volatility"] < 0.015:
                continue

            # ADAPTIVE THRESHOLD
            vol_adj = max(0.8, min(1.2, f["volatility"] * 20))
            threshold = 1.2 * vol_adj * (1 - rs * 0.2)

            if f["score"] < threshold:
                continue

            # =========================
            # RR
            # =========================
            risk = f["entry"] - f["sl"]
            if risk <= 0:
                continue

            tp = f["entry"] + risk * tp_mult
            rr = (tp - f["entry"]) / risk

            if rr > 3.0:
                tp = f["entry"] + risk * 3.0
                rr = 3.0

            if rr < rr_min:
                continue

            print(f"{symbol} | rr={rr:.2f}")

            # =========================
            # META
            # =========================
            signal = {
                "symbol": symbol,
                "rr": rr,
                "score": f["score"],
                "regime": mode,
                "correlation": rs,
                "volatility": f["volatility"],
                "liquidity": f["liquidity"],
                "type": f["type"]
            }

            prob = meta_filter_v6(signal)

            print(f"{symbol} | prob={prob:.2f}")

            if prob < meta_th:
                continue

            future_df = df_full[df_full["date"] > date].head(MAX_HOLD_DAYS)
            if future_df.empty:
                continue

            result = simulate_trade(future_df, f["entry"], f["sl"], tp)

            update_meta_v6(signal, result)

            dd = (peak_equity - equity) / peak_equity
            if dd > 0.25:
                break

            size_scale = max(0.3, prob)
            risk_amount = equity * base_risk_pct * size_scale

            if result == 1:
                equity += risk_amount * rr
            elif result == -1:
                equity -= risk_amount

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
