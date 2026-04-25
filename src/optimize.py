from backtest import run_backtest
import itertools

rs_values = [-0.08, -0.05, -0.02]
entry_ranges = [0.03, 0.05, 0.07]
leader_counts = [5, 8]

results = []

for rs, entry, leader in itertools.product(
    rs_values, entry_ranges, leader_counts
):

    print(f"TEST rs={rs}, entry={entry}, leader={leader}")

    df = run_backtest("2023-01-01")

    if len(df) < 20:
        continue

    equity = df["equity"]
    max_dd = ((equity.cummax() - equity) / equity.cummax()).max()

    score = equity.iloc[-1] / (1 + max_dd)

    results.append({
        "rs": rs,
        "entry": entry,
        "leader": leader,
        "final": equity.iloc[-1],
        "dd": max_dd,
        "score": score
    })

results = sorted(results, key=lambda x: x["score"], reverse=True)

print("\n🔥 BEST CONFIG:")
for r in results[:5]:
    print(r)
