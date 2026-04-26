import pandas as pd
import numpy as np
from data_loader import load_index


def compute_features(df):

    close = df["close"]

    returns = close.pct_change()

    vol = returns.rolling(20).std()
    trend = close.rolling(20).mean() - close.rolling(50).mean()

    drawdown = (close / close.cummax()) - 1

    return {
        "vol": vol.iloc[-1],
        "trend": trend.iloc[-1],
        "drawdown": drawdown.iloc[-1]
    }


def regime_score():

    df = load_index()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    if len(df) < 100:
        return 0

    f = compute_features(df)

    score = 0

    # 🔥 volatility
    if f["vol"] < 0.015:
        score += 1
    elif f["vol"] > 0.03:
        score -= 1

    # 🔥 trend
    if f["trend"] > 0:
        score += 1
    else:
        score -= 1

    # 🔥 drawdown
    if f["drawdown"] < -0.15:
        score -= 2

    return score


def get_regime():

    score = regime_score()

    if score <= -1:
        return "OFF"
    elif score <= 1:
        return "SAFE"
    else:
        return "AGGRESSIVE"
