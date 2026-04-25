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


def simulate_trade(df, entry, sl, tp):

    for i in range(len(df)):
        if df["low"].iloc[i] <= sl:
            return -1
        if df["high"].iloc[i] >= tp:
            return 1

    return 0


def run_backtest(start_date="2023-01-01"):

    df_symbols = load_symbols()
    df_index_full = load_index()

    equity = INITIAL_CAPITAL
    history = []

    for date in df_index_full["date"].unique():

        if date < start_date:
            continue

        df_index = df_index_full[df_index_full["date"] <= date]

        m = market_score()
        if m < 0:
            continue

        sector_df = sector_money_flow(df_symbols)
        sector_df = sector_rotation(sector_df)

        top_sectors = sector_df.head(3)

        leaders = []

        for _, row in top_sectors.iterrows():
            stocks = pick_leaders(df_symbols, row["sector"])
            for _, s in stocks.iterrows():
                leaders.append(s["symbol"])

        leaders = list(set(leaders))

        scored = []

        for symbol in leaders:

            df = load_stock_data(symbol)
            df = df[df["date"] <= date]

            if len(df) < 50:
                continue

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

        scored = sorted(scored, key=lambda x: x[1], reverse=True)

        if not scored:
            continue

        leaders = [s[0] for s in scored[:5]]

        for symbol in leaders:

            df = load_stock_data(symbol)
            df = df[df["date"] <= date]

            ok, f = validate_entry(df)

            if not ok:
                continue

            future_df = load_stock_data(symbol)
            future_df = future_df[future_df["date"] > date].head(MAX_HOLD_DAYS)

            if future_df.empty:
                continue

            result = simulate_trade(
                future_df,
                f["entry"],
                f["sl"],
                f["tp1"]
            )

            risk = equity * RISK_PER_TRADE

            if result == 1:
                profit = risk * ((f["tp1"] - f["entry"]) / (f["entry"] - f["sl"]))
                equity += profit
            elif result == -1:
                equity -= risk

            history.append({
                "date": date,
                "symbol": symbol,
                "result": result,
                "equity": equity
            })

    return pd.DataFrame(history)
