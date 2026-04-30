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

from entry_engine import entry_score

from meta_filter_v4 import meta_filter_v5
from meta_filter_v3_5 import update_model
from meta_filter_v2 import save_meta


INITIAL_CAPITAL = 100000
MAX_HOLD_DAYS = 10


# =========================
# MARKET REGIME
# =========================
def market_regime(df_index):

    close = df_index["close"]

    ret_5 = close.pct_change(5).iloc[-1]
    ret_20 = close.pct_change(20).iloc[-1]
    vol = close.pct_change().rolling(20).std().iloc[-1]

    trend = close.rolling(20).mean().iloc[-1] - close.rolling(50).mean().iloc[-1]

    score = (
        ret_5 * 2 +
        ret_20 * 1.5 -
        vol * 2 +
        (1 if trend > 0 else -1)
    )

    score = np.tanh(score * 3)

    if score > 0.3:
        return "AGGRESSIVE", score
    elif score > -0.2:
        return "NEUTRAL", score
    else:
        return "DEFENSIVE", score


# =========================
# SIMULATE
# =========================
def simulate_trade(df, entry, sl, tp):

    for i in range(len(df)):

        o = df["open"].iloc[i]
        h = df["high"].iloc[i]
        l = df["low"].iloc[i]

        if o <= sl:
            return -1
        if o >= tp:
            return 1

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
# RR
# =========================
def calc_rr(entry, sl, tp):

    risk = entry - sl
    reward = tp - entry

    if risk <= 0:
        return 0

    return reward / risk


# =========================
# BACKTEST (V4.1 FIXED)
# =========================
def run_backtest(start_date="2023-01-01"):

    start_date = pd.to_datetime(start_date)

    df_symbols = load_symbols()
    df_index_full = load_index()

    df_index_full["date"] = pd.to_datetime(df_index_full["date"], errors="coerce")
    df_index_full = df_index_full.dropna(subset=["date"])
    df_index_full = df_index_full.sort_values("date")

    equity = INITIAL_CAPITAL
    peak_equity = equity

    history = []

    unique_dates = sorted(df_index_full["date"].unique())

    symbols_all = df_symbols["symbol"].tolist()
    data_map = preload_all(symbols_all)

    for date in unique_dates:

        if date < start_date:
            continue

        peak_equity = max(peak_equity, equity)

        df_index = df_index_full[df_index_full["date"] <= date]

        if len(df_index) < 50:
            continue

        mode, _ = market_regime(df_index)

        # =========================
        # CONFIG
        # =========================
        if mode == "AGGRESSIVE":
            base_risk_pct = 0.025
            max_trades = 3
            entry_th = 1.5
        elif mode == "NEUTRAL":
            base_risk_pct = 0.015
            max_trades = 2
            entry_th = 2.0
        else:
            base_risk_pct = 0.01
            max_trades = 1
            entry_th = 2.5

        # =========================
        # SECTOR FILTER
        # =========================
        try:
            sector_df = sector_money_flow(df_symbols)
            sector_df = sector_rotation(sector_df)
        except:
            continue

        top_sectors = sector_df.head(3)

        leaders = []

        for _, row in top_sectors.iterrows():
            stocks = pick_leaders(df_symbols, row["sector"])
            leaders += stocks["symbol"].tolist()

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
                    rs * 2 +
                    voe * 1.5 +
                    inst * 1.2 +
                    inst_flow * 1.8 +
                    mf * 1.3 +
                    flow_acc * 1.2 +
                    (1 if acc else 0)
                )

                score *= (1 + np.tanh(score))

                scored.append((symbol, score, rs))

            except:
                continue

        if not scored:
            continue

        scored = sorted(scored, key=lambda x: x[1], reverse=True)
        leaders = scored[:10]

        # =========================
        # ENTRY
        # =========================
        trades_today = 0

        for symbol, _, rs in leaders:

            if trades_today >= max_trades:
                break

            df_full = data_map[symbol]
            df = df_full[df_full["date"] <= date]

            f = entry_score(df)

            if f is None:
                continue

            score_entry = f["score"]

            # ✅ FIX: dùng 1 ngưỡng duy nhất
            if score_entry < entry_th:
                continue

            rr = calc_rr(f["entry"], f["sl"], f["tp1"])

            # ✅ FIX: lọc RR chuẩn
            if rr < 1.2:
                continue

            signal = {
                "symbol": symbol,
                "type": f.get("type", "UNKNOWN"),
                "rr": rr,
                "mtf_score": score_entry,
                "regime": mode,
                "score": score_entry,
                "correlation": rs
            }

            ok_meta, prob, p2, p3 = meta_filter_v5(signal)

            # ✅ FIX: soft filter meta
            if not ok_meta and prob < 0.45:
                continue

            future_df = df_full[df_full["date"] > date].head(MAX_HOLD_DAYS)

            if future_df.empty:
                continue

            result = simulate_trade(
                future_df,
                f["entry"],
                f["sl"],
                f["tp1"]
            )

            # =========================
            # RISK CONTROL
            # =========================
            dd = (peak_equity - equity) / peak_equity if peak_equity > 0 else 0

            if dd < 0.05:
                dd_scale = 1.0
            elif dd < 0.1:
                dd_scale = 0.7
            elif dd < 0.15:
                dd_scale = 0.5
            else:
                dd_scale = 0.3

            ai_scale = 0.7 + prob
            risk_amount = equity * base_risk_pct * dd_scale * ai_scale

            # APPLY
            if result == 1:
                equity += risk_amount * rr
                perf["v2_win"] = 0.9 * perf["v2_win"] + 0.1 * p2
                perf["v3_win"] = 0.9 * perf["v3_win"] + 0.1 * p3
            elif result == -1:
                equity -= risk_amount

            # LEARN
            update_model(signal, result, equity, peak_equity)

            history.append({
                "date": date,
                "symbol": symbol,
                "result": result,
                "equity": equity,
                "rr": rr,
                "regime": mode,
                "meta_prob": prob,
                "meta_v2": p2,
                "meta_v3": p3
            })

            trades_today += 1

    save_meta()

    return pd.DataFrame(history)
