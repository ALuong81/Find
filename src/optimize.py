from backtest import run_backtest
import itertools

rs_values = [-0.08, -0.05, -0.02]
entry_ranges = [0.03, 0.05, 0.07]
flow_weights = [0.5, 1.0, 1.5]
leader_counts = [5, 8, 12]

results = []

for rs, entry, flow, leader in itertools.product(
    rs_values, entry_ranges, flow_weights, leader_counts
):

    print(f"\nTEST: rs={rs}, entry={entry}, flow={flow}, leader={leader}")

    df = run_backtest("2023-01-01")

    if len(df) < 20:
        continue

    equity = df["equity"]
    returns = equity.pct_change().dropna()

    winrate = (df["result"] == 1).mean()
    max_dd = ((equity.cummax() - equity) / equity.cummax()).max()

    score = equity.iloc[-1] / (1 + max_dd)

    results.append({
        "rs": rs,
        "entry": entry,
        "flow": flow,
        "leader": leader,
        "final": equity.iloc[-1],
        "dd": max_dd,
        "score": score
    })

# sort best
results = sorted(results, key=lambda x: x["score"], reverse=True)

print("\n🔥 TOP 5 BEST CONFIG:")
for r in results[:5]:
    print(r)
