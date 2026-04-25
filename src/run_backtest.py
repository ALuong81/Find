from backtest import run_backtest

df = run_backtest("2023-01-01")

print("\n===== RESULT =====")
print(df.tail())

print("\nFinal Equity:", df["equity"].iloc[-1])
print("Total Trades:", len(df))
print("Winrate:", (df["result"] == 1).mean())
