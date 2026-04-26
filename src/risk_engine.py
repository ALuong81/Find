import numpy as np


# =========================
# 🔥 EDGE CALCULATION
# =========================
def calc_edge(signal):

    score = signal.get("score", 0)
    confidence = signal.get("confidence", 0.5)
    mtf = signal.get("mtf_score", 0)

    # normalize score
    score_norm = np.tanh(score / 5)

    edge = (
        score_norm * 0.5 +
        confidence * 0.3 +
        mtf * 0.2
    )

    return np.clip(edge, 0.2, 1.0)


# =========================
# 🔥 TYPE WEIGHT
# =========================
def type_weight(signal):

    t = signal.get("type", "")

    weights = {
        "EARLY_BREAKOUT": 1.2,
        "PRE": 1.1,
        "EARLY": 1.0,
        "STRONG": 0.9,
        "PULLBACK": 0.7
    }

    return weights.get(t, 0.8)


# =========================
# 🔥 RR ADJUST
# =========================
def rr_weight(signal):

    rr = signal.get("rr", 1)

    if rr >= 2:
        return 1.2
    elif rr >= 1:
        return 1.0
    else:
        return 0.6


# =========================
# 🔥 REGIME ADJUST
# =========================
def regime_adjust(regime):

    if regime == "AGGRESSIVE":
        return 1.2
    elif regime == "NEUTRAL":
        return 1.0
    else:  # DEFENSIVE
        return 0.6


# =========================
# 🔥 FINAL POSITION SIZE (CORE)
# =========================
def position_size(equity, signal, regime, base_risk=0.02):

    entry = signal["entry"]
    sl = signal["sl"]

    if entry == sl:
        return 0

    # =========================
    # 🔥 CALC RISK %
    # =========================
    edge = calc_edge(signal)
    t_weight = type_weight(signal)
    rr_adj = rr_weight(signal)
    regime_adj = regime_adjust(regime)

    risk_pct = base_risk * edge * t_weight * rr_adj * regime_adj

    # clamp tránh quá lớn / quá nhỏ
    risk_pct = np.clip(risk_pct, 0.005, base_risk)

    # =========================
    # 🔥 POSITION SIZE
    # =========================
    risk_amount = equity * risk_pct
    size = risk_amount / abs(entry - sl)

    return round(size, 2)


# =========================
# 🔥 OPTIONAL: MAX TOTAL RISK CONTROL
# =========================
def cap_total_risk(positions, max_total_risk=0.06):

    total = sum(p["risk_pct"] for p in positions)

    if total <= max_total_risk:
        return positions

    scale = max_total_risk / total

    for p in positions:
        p["risk_pct"] *= scale
        p["size"] *= scale

    return positions
