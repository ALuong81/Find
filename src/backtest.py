import pandas as pd
from data_loader import load_stock_data, load_index
from symbol_loader import load_symbols

from smart_money import market_score, sector_money_flow, pick_leaders
from sector_rotation import sector_rotation
from relative_strength import relative_strength
from entry import validate_entry
from voe import voe_score
from accumulation import detect_accumulation
from institutional import institutional_score
from money_flow import money_flow_score

INITIAL_CAPITAL = 100000
RISK_PER_TRADE = 0.02
MAX_HOLD_DAYS = 10


# =========================
# SIMULATE TRADE
# =========================
def simulate_trade(df, entry, sl, tp):

    for i in range(len(df)):
        low = df["low"].iloc[i]
        high = df["high"].iloc[i]

        if low <= sl:
            return -1

        if high >= tp:
            return 1

    return 0


# =========================
# PRELOAD ALL DATA (🔥 tối ưu)
# =========================
def preload_all(symbols):

    data_map = {}

    for symbol in symbols:
        try:
            df = load_stock_data(symbol)

            if df is None or df.empty:
                continue

            # 🔥 FIX DATETIME TRIỆT ĐỂ
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
def run_backtest(start_date="2023-01-01"):

    start_date = pd.to_datetime(start_date)

    df_symbols = load_symbols()
    df_index_full = load_index()

    # 🔥 FIX datetime index
    df_index_full["date"] = pd.to_datetime(df_index_full["date"], errors="coerce")
    df_index_full = df_index_full.dropna(subset=["date"])
    df_index_full = df_index_full.sort_values("date")

    equity = INITIAL_CAPITAL
    history = []

    unique_dates = df_index_full["date"].unique()

    # 🔥 PRELOAD DATA 1 LẦN (cực quan trọng)
    symbols_all = df_symbols["symbol"].tolist()
    data_map = preload_all(symbols_all)

    for date in unique_dates:

        if date < start_date:
            continue

        # =========================
        # MARKET
        # =========================
        df_index = df_index_full[df_index_full["date"] <= date]

        m = market_score()
        if m < 0:
            continue

        # =========================
        # SECTOR
        # =========================
        sector_df = sector_money_flow(df_symbols)
        sector_df = sector_rotation(sector_df)

        top_sectors = sector_df.head(3)

        leaders = []

        for _, row in top_sectors.iterrows():
            stocks = pick_leaders(df_symbols, row["sector"])
            for _, s in stocks.iterrows():
                leaders.append(s["symbol"])

        leaders = list(set(leaders))

        # =========================
        # FILTER
        # =========================
        scored = []

        for symbol in leaders:

            if symbol not in data_map:
                continue

            df_full = data_map[symbol]

            # 🔥 NO LOOKAHEAD
            df = df_full[df_full["date"] <= date]

            if len(df) < 50:
                continue

            try:
                rs = relative_strength(df, df_index)
                voe = voe_score(df, df_index)
                inst = institutional_score(df)
                mf = money_flow_score(df)
                acc = detect_accumulation(df)

                if rs > -0.05:

                    score = (
                        rs * 2 +
                        voe * 1.5 +
                        inst * 1.5 +
                        mf * 1.2 +
                        (1 if acc else 0)
                    )

                    scored.append((symbol, score))

            except:
                continue

        scored = sorted(scored, key=lambda x: x[1], reverse=True)

        if not scored:
            continue

        leaders = [s[0] for s in scored[:5]]

        # =========================
        # ENTRY
        # =========================
        for symbol in leaders:

            if symbol not in data_map:
                continue

            df_full = data_map[symbol]

            df = df_full[df_full["date"] <= date]

            if len(df) < 50:
                continue

            ok, f = validate_entry(df, symbol)

            if not ok:
                continue

            # =========================
            # FUTURE DATA
            # =========================
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
            # POSITION SIZING
            # =========================
            risk = equity * RISK_PER_TRADE

            if result == 1:
                rr = (f["tp1"] - f["entry"]) / (f["entry"] - f["sl"])
                equity += risk * rr

            elif result == -1:
                equity -= risk

            history.append({
                "date": date,
                "symbol": symbol,
                "result": result,
                "equity": equity
            })

    return pd.DataFrame(history)
