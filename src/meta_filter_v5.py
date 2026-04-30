import numpy as np

from meta_filter_v2 import meta_filter_v2
from meta_filter_v3_5 import meta_filter_v3_5


# =========================
# CONFIG
# =========================
BASE_THRESHOLD = 0.50
DEBUG = True


# =========================
# PERFORMANCE MEMORY (simple online)
# =========================
perf = {
    "v2_win": 0.5,
    "v3_win": 0.5
}


# =========================
# WEIGHTING (V5)
# =========================
def get_weights(signal, conf):

    regime = signal.get("regime", "NEUTRAL")
    rr = signal.get("rr", 1)
    mtf = signal.get("mtf_score", 0)

    # base
    w_v2 = 0.5 * perf["v2_win"]
    w_v3 = 0.5 * perf["v3_win"]

    # regime bias
    if regime == "AGGRESSIVE":
        w_v3 += 0.2
    elif regime == "DEFENSIVE":
        w_v2 += 0.2

    # RR bias
    if rr > 2:
        w_v3 += 0.1

    # MTF bias
    if mtf > 2:
        w_v3 += 0.1

    # CONFIDENCE BOOST
    if conf > 0.5:
        w_v2 += 0.1
        w_v3 += 0.1

    total = w_v2 + w_v3
    return w_v2 / total, w_v3 / total


# =========================
# DISAGREEMENT PENALTY (SOFT)
# =========================
def disagreement_penalty(p1, p2):

    diff = abs(p1 - p2)

    if diff < 0.1:
        return 1.0
    elif diff < 0.2:
        return 0.9
    elif diff < 0.3:
        return 0.8
    else:
        return 0.7   # 🔥 mềm hơn V4 (tránh kill tín hiệu)


# =========================
# DYNAMIC THRESHOLD (SMART)
# =========================
def get_threshold(signal):

    regime = signal.get("regime", "NEUTRAL")
    rr = signal.get("rr", 1)
    mtf = signal.get("mtf_score", 0)

    th = BASE_THRESHOLD

    if regime == "AGGRESSIVE":
        th -= 0.08
    elif regime == "DEFENSIVE":
        th -= 0.05

    # high RR → dễ vào hơn
    if rr > 2:
        th -= 0.05

    # strong setup → dễ vào
    if mtf > 2:
        th -= 0.05

    return th


# =========================
# DEBUG
# =========================
def debug_log(signal, prob, prob2, prob3, th, conf, w2, w3):

    if not DEBUG:
        return

    print(
        f"[META V5] {signal.get('symbol','?')} | "
        f"prob={prob:.3f} | v2={prob2:.3f} | v3={prob3:.3f} | "
        f"w2={w2:.2f} | w3={w3:.2f} | "
        f"th={th:.3f} | conf={conf:.3f} | "
        f"rr={signal.get('rr',0):.2f} | "
        f"regime={signal.get('regime')}"
    )


# =========================
# MAIN
# =========================
def meta_filter_v5(signal):

    # =========================
    # MODEL OUTPUT
    # =========================
    ok2, score2, wr, conf = meta_filter_v2(signal)
    ok3, prob3 = meta_filter_v3_5(signal)

    prob2 = np.clip(score2, 0, 1)

    # =========================
    # WEIGHT
    # =========================
    w2, w3 = get_weights(signal, conf)

    # =========================
    # COMBINE
    # =========================
    prob = w2 * prob2 + w3 * prob3

    # =========================
    # DISAGREEMENT
    # =========================
    if conf >= 0.4:
        penalty = disagreement_penalty(prob2, prob3)
        prob *= penalty

    # =========================
    # THRESHOLD
    # =========================
    th = get_threshold(signal)

    # =========================
    # DEBUG
    # =========================
    debug_log(signal, prob, prob2, prob3, th, conf, w2, w3)

    # =========================
    # LOW CONF → SOFT MODE
    # =========================
    if conf < 0.35:
        return True, prob, prob2, prob3

    # =========================
    # DECISION
    # =========================
    if prob < th:
        return False, prob, prob2, prob3

    return True, prob, prob2, prob3
