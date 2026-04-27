import numpy as np
import pandas as pd
import os


HISTORY_FILE = "trade_history.csv"

# Bayesian prior (neutral)
ALPHA = 5
BETA = 5


# =========================
# SAVE TRADE
# =========================
def record_trade(signal, result):

    row = {
        "type": signal["type"],
        "rr": signal["rr"],
        "mtf": signal.get("mtf_score", 0),
        "regime": signal.get("regime", "NEUTRAL"),
        "result": result
    }

    df = pd.DataFrame([row])

    if os.path.exists(HISTORY_FILE):
        df.to_csv(HISTORY_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(HISTORY_FILE, index=False)


# =========================
# BUCKET HELPERS
# =========================
def bucket_rr(rr):
    if rr < 1:
        return "low"
    elif rr < 2:
        return "mid"
    else:
        return "high"


def bucket_mtf(mtf):
    if mtf < 0:
        return "neg"
    elif mtf < 0.5:
        return "neutral"
    else:
        return "strong"


# =========================
# LOAD + GROUP
# =========================
def load_stats():

    if not os.path.exists(HISTORY_FILE):
        return {}

    df = pd.read_csv(HISTORY_FILE)

    df["rr_bin"] = df["rr"].apply(bucket_rr)
    df["mtf_bin"] = df["mtf"].apply(bucket_mtf)

    grouped = df.groupby(["type", "rr_bin", "mtf_bin", "regime"])

    stats = {}

    for key, g in grouped:
        wins = (g["result"] == 1).sum()
        total = len(g)

        stats[key] = (wins, total)

    return stats


# =========================
# ESTIMATE WINRATE
# =========================
def estimate_winrate(signal):

    stats = load_stats()

    key = (
        signal["type"],
        bucket_rr(signal["rr"]),
        bucket_mtf(signal.get("mtf_score", 0)),
        signal.get("regime", "NEUTRAL")
    )

    if key not in stats:
        # fallback baseline
        return 0.45

    wins, total = stats[key]

    # Bayesian smoothing
    winrate = (wins + ALPHA) / (total + ALPHA + BETA)

    return float(winrate)
