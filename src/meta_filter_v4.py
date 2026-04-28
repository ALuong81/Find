import numpy as np

from meta_filter_v2 import meta_filter_v2
from meta_filter_v3_5 import meta_filter_v3_5


# =========================
# CONFIG
# =========================
BASE_THRESHOLD = 0.55


# =========================
# WEIGHTING
# =========================
def get_weights(signal):

    regime = signal.get("regime", "NEUTRAL")
    rr = signal.get("rr", 1)
    mtf = signal.get("mtf_score", 0)

    # base
    w_v2 = 0.5
    w_v3 = 0.5

    # =========================
    # REGIME ADAPT
    # =========================
    if regime == "AGGRESSIVE":
        w_v3 += 0.2   # trust ML hơn
    elif regime == "DEFENSIVE":
        w_v2 += 0.2   # trust rule hơn

    # =========================
    # FEATURE ADAPT
    # =========================
    if rr > 2:
        w_v3 += 0.1

    if mtf > 0:
        w_v3 += 0.1

    # normalize
    total = w_v2 + w_v3
    return w_v2 / total, w_v3 / total


# =========================
# DISAGREEMENT PENALTY
# =========================
def disagreement_penalty(p1, p2):

    diff = abs(p1 - p2)

    if diff < 0.1:
        return 1.0
    elif diff < 0.2:
        return 0.85
    elif diff < 0.3:
        return 0.7
    else:
        return 0.5   # 🔥 conflict lớn → giảm mạnh


# =========================
# DYNAMIC THRESHOLD
# =========================
def get_threshold(signal):

    regime = signal.get("regime", "NEUTRAL")

    th = BASE_THRESHOLD

    if regime == "AGGRESSIVE":
        th -= 0.05
    elif regime == "DEFENSIVE":
        th += 0.08

    return th


# =========================
# MAIN ENSEMBLE
# =========================
def meta_filter_v4(signal):

    # =========================
    # MODEL OUTPUT
    # =========================
    ok2, score2, wr, conf = meta_filter_v2(signal)
    ok3, prob3 = meta_filter_v3_5(signal)

    # normalize V2 score về prob-like
    prob2 = np.clip(score2, 0, 1)

    # =========================
    # WEIGHT
    # =========================
    w2, w3 = get_weights(signal)

    # =========================
    # COMBINE
    # =========================
    prob = w2 * prob2 + w3 * prob3

    # =========================
    # DISAGREEMENT CONTROL
    # =========================
    penalty = disagreement_penalty(prob2, prob3)
    prob *= penalty

    # =========================
    # FINAL DECISION
    # =========================
    th = get_threshold(signal)

    if prob < th:
        return False, prob, prob2, prob3

    return True, prob, prob2, prob3
