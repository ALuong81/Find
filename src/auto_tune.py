import numpy as np
import pandas as pd
from backtest import run_backtest


# =========================
# PARAM SPACE
# =========================
def sample_config():

    return {
        "vol_min": np.random.uniform(0.015, 0.04),
        "breakout_buffer": np.random.uniform(0.95, 1.0),
        "rsi_max": np.random.uniform(75, 90),
        "tp_base": np.random.uniform(1.5, 2.5),
        "tp_vol_factor": np.random.uniform(5, 15)
    }


# =========================
# METRIC
# =========================
def evaluate(df):

    if len(df) < 20:
        return -999

    returns = df["equity"].pct_change().fillna(0)

    sharpe = returns.mean() / (returns.std() + 1e-9)
    total_return = df["equity"].iloc[-1] / df["equity"].iloc[0] - 1
    drawdown = (df["equity"].cummax() - df["equity"]).max()

    score = sharpe * 2 + total_return - drawdown * 2

    return score


# =========================
# AUTO TUNE
# =========================
def auto_tune(n_iter=50):

    best_score = -999
    best_config = None

    for i in range(n_iter):

        config = sample_config()

        print(f"\n=== RUN {i} ===")
        print(config)

        try:
            df = run_backtest(config)

            score = evaluate(df)

            print(f"SCORE = {score:.4f}")

            if score > best_score:
                best_score = score
                best_config = config

        except Exception as e:
            print("ERROR:", e)
            continue

    print("\n🔥 BEST CONFIG:")
    print(best_config)
    print("BEST SCORE:", best_score)

    return best_config
