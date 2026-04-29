import numpy as np

from meta_filter_v2 import meta_filter_v2
from meta_filter_v3_5 import meta_filter_v3_5


# =========================
# CONFIG
# =========================
BASE_THRESHOLD = 0.48
DEBUG = True   # 🔥 bật/tắt debug tại đây


# =========================
# WEIGHTING
# =========================
def get_weights(signal):

    regime = signal.get("regime", "NEUTRAL")
    rr = signal.get("rr", 1)
    mtf = signal.get("mtf_score", 0)

    w_v2 = 0.5
    w_v3 = 0.5

    if regime == "AGGRESSIVE":
        w_v3 += 0.2
    elif regime == "DEFENSIVE":
        w_v2 += 0.2

    if rr > 2:
        w_v3 += 0.1

    if mtf > 0:
        w_v3 += 0.1

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
        return 0.8
    else:
        return 0.6


# =========================
# DYNAMIC THRESHOLD
# =========================
def get_threshold(signal):

    regime = signal.get("regime", "NEUTRAL")

    th = BASE_THRESHOLD

    if regime == "AGGRESSIVE":
        th -= 0.07
    elif regime == "DEFENSIVE":
        th -= 0.08

    return th


# =========================
# DEBUG LOGGER
# =========================
def debug_log(signal, prob, prob2, prob3, th, conf):

    if not DEBUG:
        return

    print(
        f"[META V4] {signal.get('symbol','?')} | "
        f"prob={prob:.3f} | v2={prob2:.3f} | v3={prob3:.3f} | "
        f"th={th:.3f} | conf={conf:.3f} | "
        f"rr={signal.get('rr',0):.2f} | "
        f"regime={signal.get('regime')}"
    )


# =========================
# MAIN ENSEMBLE
# =========================
def meta_filter_v4(signal):

    # =========================
    # MODEL OUTPUT
    # =========================
    ok2, score2, wr, conf = meta_filter_v2(signal)
    ok3, prob3 = meta_filter_v3_5(signal)

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
    # THRESHOLD
    # =========================
    th = get_threshold(signal)

    # =========================
    # DEBUG
    # =========================
    debug_log(signal, prob, prob2, prob3, th, conf)

    # =========================
    # LOW CONF → SOFT MODE
    # =========================
    if conf < 0.35:
        if prob > (th - 0.05):
            return True, prob, prob2, prob3
        else:
            return False, prob, prob2, prob3

    # =========================
    # NORMAL DECISION
    # =========================
    if prob < th:
        return False, prob, prob2, prob3

    return True, prob, prob2, prob3
