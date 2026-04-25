from backtest import run_backtest
import numpy as np

df = run_backtest("2023-01-01")

equity = df["equity"]

returns = equity.pct_change().dropna()

winrate = (df["result"] == 1).mean()
avg_win = returns[returns > 0].mean()
avg_loss = returns[returns < 0].mean()

expectancy = winrate * avg_win + (1 - winrate) * avg_loss
max_dd = ((equity.cummax() - equity) / equity.cummax()).max()

sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else 0

print("\n===== RESULT =====")
print("Final Equity:", equity.iloc[-1])
print("Total Trades:", len(df))
print("Winrate:", round(winrate, 3))
print("Expectancy:", round(expectancy, 4))
print("Max Drawdown:", round(max_dd, 3))
print("Sharpe:", round(sharpe, 2))
