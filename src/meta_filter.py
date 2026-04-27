import numpy as np
from adaptive_winrate import estimate_winrate


# =========================
# CONFIG
# =========================
META_THRESHOLD = 0.55


# =========================
# TYPE WEIGHT
# =========================
TYPE_WEIGHT = {
    "EARLY_BREAKOUT": 1.0,
    "PRE": 0.9,
    "EARLY": 0.8,
    "STRONG": 0.7,
    "PULLBACK": 0.6
}


# =========================
# META SCORE
# =========================
def compute_meta_score(signal, regime):

    rr = signal.get("rr", 1)
    mtf = signal.get("mtf_score", 0)
    type_ = signal.get("type", "UNKNOWN")

    # =========================
    # 1. SIGNAL QUALITY
    # =========================
    type_score = TYPE_WEIGHT.get(type_, 0.5)

    rr_score = np.tanh(rr / 2)
    mtf_score = np.tanh(mtf)

    quality = 0.4 * type_score + 0.4 * rr_score + 0.2 * mtf_score

    # =========================
    # 2. REGIME
    # =========================
    regime_score = {
        "AGGRESSIVE": 1.0,
        "NEUTRAL": 0.7,
        "DEFENSIVE": 0.4
    }.get(regime, 0.5)

    # =========================
    # 3. AI WINRATE
    # =========================
    winrate = estimate_winrate(signal)
    edge = np.tanh((winrate - 0.5) * 5)

    # =========================
    # FINAL META SCORE
    # =========================
    meta_score = (
        quality * 0.5 +
        regime_score * 0.2 +
        edge * 0.3
    )

    return meta_score


# =========================
# FILTER
# =========================
def meta_filter(signal, regime):

    score = compute_meta_score(signal, regime)

    if score < META_THRESHOLD:
        return False, score

    return True, score
