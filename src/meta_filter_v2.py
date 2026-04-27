import numpy as np
from collections import defaultdict

# =========================
# CONFIG
# =========================
BASE_THRESHOLD = 0.55
MIN_SAMPLES = 5
DECAY = 0.97  # memory decay (for future extension)


# =========================
# STORAGE (in-memory)
# =========================
stats = defaultdict(lambda: {"win": 0, "loss": 0})


# =========================
# KEY BUILDER
# =========================
def build_key(signal):

    rr = signal.get("rr", 1)
    type_ = signal.get("type", "UNK")
    regime = signal.get("regime", "UNK")
    mtf = signal.get("mtf_score", 0)

    # bucket hóa
    rr_bucket = round(min(rr, 3))        # 1,2,3
    mtf_bucket = int(mtf > 0)            # 0/1

    return f"{type_}|{regime}|rr{rr_bucket}|mtf{mtf_bucket}"


# =========================
# UPDATE AFTER TRADE
# =========================
def update_meta(signal, result):

    key = build_key(signal)

    if result == 1:
        stats[key]["win"] += 1
    elif result == -1:
        stats[key]["loss"] += 1


# =========================
# BAYES WINRATE
# =========================
def bayes_winrate(win, loss):

    # Beta prior (1,1) → không bias
    return (win + 1) / (win + loss + 2)


# =========================
# CONFIDENCE
# =========================
def confidence(win, loss):

    n = win + loss

    if n < MIN_SAMPLES:
        return 0.3  # low trust

    return np.tanh(n / 20)  # saturate


# =========================
# META SCORE V2
# =========================
def compute_meta_score(signal):

    key = build_key(signal)
    data = stats[key]

    win = data["win"]
    loss = data["loss"]

    wr = bayes_winrate(win, loss)
    conf = confidence(win, loss)

    rr = signal.get("rr", 1)
    mtf = signal.get("mtf_score", 0)

    # =========================
    # COMPONENTS
    # =========================
    rr_score = np.tanh(rr / 2)
    mtf_score = np.tanh(mtf)

    edge = np.tanh((wr - 0.5) * 5)

    # =========================
    # FINAL
    # =========================
    meta = (
        0.35 * rr_score +
        0.25 * mtf_score +
        0.25 * edge * conf +   # quan trọng
        0.15 * wr
    )

    return meta, wr, conf


# =========================
# ADAPTIVE THRESHOLD
# =========================
def get_threshold(regime):

    if regime == "AGGRESSIVE":
        return BASE_THRESHOLD - 0.05
    elif regime == "NEUTRAL":
        return BASE_THRESHOLD
    else:
        return BASE_THRESHOLD + 0.1


# =========================
# FILTER
# =========================
def meta_filter_v2(signal):

    regime = signal.get("regime", "NEUTRAL")

    score, wr, conf = compute_meta_score(signal)
    th = get_threshold(regime)

    if score < th:
        return False, score, wr, conf

    return True, score, wr, conf
