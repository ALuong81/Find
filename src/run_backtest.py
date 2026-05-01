from backtest import run_backtest, DEFAULT_CONFIG
import numpy as np
import pandas as pd


def main():

    print("🚀 START BACKTEST")

    # =========================
    # CONFIG (có thể tuning sau)
    # =========================
    config = DEFAULT_CONFIG.copy()

    # ví dụ tweak nhanh:
    # config["vol_min"] = 0.025
    # config["meta_threshold"] = 0.55

    # =========================
    # RUN (🔥 gọi đúng param)
    # =========================
    df = run_backtest(
        start_date="2023-01-01",
        config=config
    )

    if df is None or df.empty:
        print("⚠️ NO TRADE DATA")
        return

    # =========================
    # EQUITY
    # =========================
    equity = df["equity"]

    # =========================
    # RETURNS
    # =========================
    returns = equity.pct_change().dropna()

    # =========================
    # METRICS
    # =========================
    total_trades = len(df)
    winrate = (df["result"] == 1).mean()

    avg_win = returns[returns > 0].mean() if not returns[returns > 0].empty else 0
    avg_loss = returns[returns < 0].mean() if not returns[returns < 0].empty else 0

    expectancy = winrate * avg_win + (1 - winrate) * avg_loss

    max_dd = ((equity.cummax() - equity) / equity.cummax()).max()

    sharpe = 0
    if returns.std() != 0:
        sharpe = returns.mean() / returns.std() * np.sqrt(252)

    # =========================
    # PRINT RESULT
    # =========================
    print("\n===== RESULT =====")
    print("Final Equity:", round(equity.iloc[-1], 2))
    print("Total Trades:", total_trades)
    print("Winrate:", round(winrate, 3))
    print("Expectancy:", round(expectancy, 4))
    print("Max Drawdown:", round(max_dd, 3))
    print("Sharpe:", round(sharpe, 2))

    # =========================
    # SAVE FILE
    # =========================
    try:
        df.to_csv("backtest_result.csv", index=False)
        print("\n💾 Saved: backtest_result.csv")
    except Exception as e:
        print("❌ SAVE ERROR:", str(e))

    # =========================
    # EXTRA DEBUG
    # =========================
    print("\n===== LAST 5 TRADES =====")
    print(df.tail())

    # =========================
    # QUICK INSIGHT (🔥 thêm)
    # =========================
    print("\n===== QUICK STATS =====")
    print("Avg RR:", round(df["rr"].mean(), 2))
    print("Avg Meta Prob:", round(df["meta_prob"].mean(), 3))


if __name__ == "__main__":
    main()
