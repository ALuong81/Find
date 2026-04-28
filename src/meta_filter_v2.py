import numpy as np
import json
from collections import defaultdict

# =========================
# CONFIG
# =========================
BASE_THRESHOLD = 0.55
MIN_SAMPLES = 5
DECAY = 0.97  # memory decay

META_FILE = "meta_stats.json"


# =========================
# STORAGE (PERSISTENT)
# =========================
stats = defaultdict(lambda: {"win": 0.0, "loss": 0.0})


# =========================
# LOAD / SAVE
# =========================
def save_meta():
    try:
        with open(META_FILE, "w") as f:
            json.dump(dict(stats), f)
    except Exception as e:
        print("❌ SAVE META ERROR:", str(e))


def load_meta():
    global stats
    try:
        with open(META_FILE, "r") as f:
            data = json.load(f)

            for k, v in data.items():
                stats[k]["win"] = v.get("win", 0)
                stats[k]["loss"] = v.get("loss", 0)

        print("✅ META LOADED:", len(stats), "patterns")

    except Exception as e:
        print("⚠️ NO META FILE → INIT NEW", str(e))

# 🔥 LOAD NGAY KHI IMPORT
load_meta()


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

    # =========================
    # DECAY (giảm ảnh hưởng quá khứ)
    # =========================
    stats[key]["win"] *= DECAY
    stats[key]["loss"] *= DECAY

    # =========================
    # UPDATE
    # =========================
    if result == 1:
        stats[key]["win"] += 1
    elif result == -1:
        stats[key]["loss"] += 1

    # =========================
    # SAVE
    # =========================
    save_meta()


# =========================
# BAYES WINRATE
# =========================
def bayes_winrate(win, loss):

    return (win + 1) / (win + loss + 2)


# =========================
# CONFIDENCE
# =========================
def confidence(win, loss):

    n = win + loss

    if n < MIN_SAMPLES:
        return 0.3

    return np.tanh(n / 20)


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
    # FINAL SCORE
    # =========================
    meta = (
        0.35 * rr_score +
        0.25 * mtf_score +
        0.25 * edge * conf +
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
        return BASE_THRESHOLD + 0.03


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
