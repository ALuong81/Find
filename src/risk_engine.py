import numpy as np
from adaptive_winrate import estimate_winrate


# =========================
# CONFIG
# =========================
KELLY_FRACTION = 0.5     # 🔥 half Kelly
MAX_RISK_PER_TRADE = 0.03
TARGET_VOL = 0.12        # annualized target
VOL_LOOKBACK = 20


# =========================
# KELLY FRACTION
# =========================
def kelly_fraction(rr, winrate):

    b = rr
    p = winrate
    q = 1 - p

    if b <= 0:
        return 0

    k = (b * p - q) / b

    return max(k, 0) * KELLY_FRACTION


# =========================
# VOLATILITY
# =========================
def compute_volatility(df):

    returns = df["close"].pct_change().dropna()

    if len(returns) < VOL_LOOKBACK:
        return 0.02

    vol = returns.rolling(VOL_LOOKBACK).std().iloc[-1]

    # annualize (rough)
    vol = vol * np.sqrt(252)

    return max(vol, 0.01)


# =========================
# VOL ADJUST
# =========================
def volatility_adjustment(vol):

    if vol == 0:
        return 1

    adj = TARGET_VOL / vol

    return np.clip(adj, 0.5, 1.5)


# =========================
# REGIME SCALE
# =========================
def regime_scale(mode):

    if mode == "AGGRESSIVE":
        return 1.2
    elif mode == "NEUTRAL":
        return 1.0
    else:
        return 0.6


# =========================
# FINAL POSITION SIZE
# =========================
def position_size(equity, signal, mode, df):

    entry = signal["entry"]
    sl = signal["sl"]
    rr = signal["rr"]

    risk_per_share = abs(entry - sl)

    if risk_per_share <= 0:
        return 0

    # =========================
    # EDGE
    # =========================
    winrate = estimate_winrate(signal)
    kelly = kelly_fraction(rr, winrate)

    # =========================
    # VOL
    # =========================
    vol = compute_volatility(df)
    vol_adj = volatility_adjustment(vol)

    # =========================
    # REGIME
    # =========================
    reg = regime_scale(mode)

    # =========================
    # FINAL RISK %
    # =========================
    risk_pct = kelly * vol_adj * reg

    # cap lại cho an toàn
    risk_pct = min(risk_pct, MAX_RISK_PER_TRADE)

    # =========================
    # SIZE
    # =========================
    risk_amount = equity * risk_pct

    size = risk_amount / risk_per_share

    return max(size, 0)
