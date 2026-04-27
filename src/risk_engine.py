import numpy as np
from adaptive_winrate import estimate_winrate


# =========================
# CONFIG
# =========================
MAX_RISK_PER_TRADE = 0.02   # 2%
KELLY_FRACTION = 0.5        # dùng 50% Kelly
MIN_RISK = 0.002           # floor 0.2%
MAX_POSITION = 0.3         # max 30% vốn

TARGET_VOL = 0.12          # annualized target vol
VOL_LOOKBACK = 20


# =========================
# KELLY CALC
# =========================
def kelly_fraction(winrate, rr):

    if rr <= 0:
        return 0

    k = winrate - (1 - winrate) / rr

    return max(k, 0)


# =========================
# VOLATILITY
# =========================
def compute_volatility(df):

    try:
        returns = df["close"].pct_change().dropna()

        if len(returns) < VOL_LOOKBACK:
            return 0.02

        vol = returns.rolling(VOL_LOOKBACK).std().iloc[-1]

        # annualize
        vol = vol * np.sqrt(252)

        return max(vol, 0.01)

    except:
        return 0.02


# =========================
# VOL ADJUST
# =========================
def volatility_adjustment(vol):

    if vol <= 0:
        return 1

    adj = TARGET_VOL / vol

    # tránh scale quá mạnh
    return np.clip(adj, 0.5, 1.5)

def drawdown_adjustment(equity, peak):

    dd = (peak - equity) / peak

    if dd < 0.05:
        return 1.0
    elif dd < 0.1:
        return 0.8
    elif dd < 0.15:
        return 0.6
    else:
        return 0.4
        
# =========================
# MAIN POSITION SIZE
# =========================
def position_size(equity, signal, regime, df):

    entry = signal["entry"]
    sl = signal["sl"]
    rr = signal["rr"]

    risk_per_share = abs(entry - sl)

    if risk_per_share <= 0:
        return 0

    # =========================
    # 🔥 ADAPTIVE WINRATE
    # =========================
    winrate = estimate_winrate(signal)

    # =========================
    # 🔥 KELLY
    # =========================
    kelly = kelly_fraction(winrate, rr)
    kelly_adj = kelly * KELLY_FRACTION

    # =========================
    # 🔥 REGIME SCALE
    # =========================
    regime_map = {
        "AGGRESSIVE": 1.0,
        "NEUTRAL": 0.7,
        "DEFENSIVE": 0.4
    }

    regime_scale = regime_map.get(regime, 0.7)

    # =========================
    # 🔥 VOL ADJUST
    # =========================
    vol = compute_volatility(df)
    vol_adj = volatility_adjustment(vol)

    # =========================
    # 🔥 FINAL RISK %
    # =========================
    risk_pct = kelly_adj * regime_scale * vol_adj

    # clamp: cực kỳ quan trọng
    risk_pct = max(MIN_RISK, min(risk_pct, MAX_RISK_PER_TRADE))

    # =========================
    # 🔥 SIZE
    # =========================
    risk_amount = equity * risk_pct
    size = risk_amount / risk_per_share

    # =========================
    # 🔥 POSITION CAP
    # =========================
    max_size = (equity * MAX_POSITION) / entry
    size = min(size, max_size)

    return max(size, 0)
