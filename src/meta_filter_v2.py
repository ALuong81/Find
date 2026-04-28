import numpy as np
import json
import os
from collections import defaultdict

# =========================
# CONFIG
# =========================
BASE_THRESHOLD = 0.48
MIN_SAMPLES = 5
DECAY = 0.97

META_FILE = "meta_stats.json"


# =========================
# STORAGE
# =========================
stats = defaultdict(lambda: {"win": 0.0, "loss": 0.0})

def is_cold_start():
    total = sum(v["win"] + v["loss"] for v in stats.values())
    return total < 30
    
# =========================
# LOAD / SAVE (SAFE)
# =========================
def load_meta():

    global stats

    if not os.path.exists(META_FILE):
        print("⚠️ META FILE NOT FOUND → INIT NEW")
        return

    try:
        with open(META_FILE, "r") as f:
            data = json.load(f)

        for k, v in data.items():
            stats[k]["win"] = float(v.get("win", 0))
            stats[k]["loss"] = float(v.get("loss", 0))

        print(f"✅ META LOADED: {len(stats)} patterns")

    except Exception as e:
        print("❌ LOAD META ERROR:", str(e))


def save_meta():

    try:
        with open(META_FILE, "w") as f:
            json.dump(dict(stats), f)

    except Exception as e:
        print("❌ SAVE META ERROR:", str(e))


# ⚠️ CHỈ LOAD 1 LẦN DUY NHẤT
_meta_loaded = False

def ensure_meta_loaded():
    global _meta_loaded
    if not _meta_loaded:
        load_meta()
        _meta_loaded = True


# =========================
# KEY BUILDER (IMPROVED)
# =========================
def build_key(signal):

    rr = signal.get("rr", 1)
    type_ = signal.get("type", "UNK")
    regime = signal.get("regime", "UNK")
    mtf = signal.get("mtf_score", 0)
    meta_hint = signal.get("score", 0)

    rr_bucket = round(min(rr, 3))
    mtf_bucket = int(mtf > 0)
    score_bucket = int(meta_hint > 1.5)

    return f"{type_}|{regime}|rr{rr_bucket}|mtf{mtf_bucket}|s{score_bucket}"


# =========================
# UPDATE AFTER TRADE
# =========================
def update_meta(signal, result):

    ensure_meta_loaded()

    key = build_key(signal)

    # DECAY
    stats[key]["win"] *= DECAY
    stats[key]["loss"] *= DECAY

    # UPDATE
    if result == 1:
        stats[key]["win"] += 1
    elif result == -1:
        stats[key]["loss"] += 1


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
# META SCORE
# =========================
def compute_meta_score(signal):

    ensure_meta_loaded()

    key = build_key(signal)
    data = stats[key]

    win = data["win"]
    loss = data["loss"]

    wr = bayes_winrate(win, loss)
    conf = confidence(win, loss)

    rr = signal.get("rr", 1)
    mtf = signal.get("mtf_score", 0)

    # components
    rr_score = np.tanh(rr / 2)
    mtf_score = np.tanh(mtf)
    edge = np.tanh((wr - 0.5) * 5)

    meta = (
        0.35 * rr_score +
        0.25 * mtf_score +
        0.25 * edge * conf +
        0.15 * wr
    )

    return meta, wr, conf


# =========================
# THRESHOLD
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

    ensure_meta_loaded()

    regime = signal.get("regime", "NEUTRAL")

    score, wr, conf = compute_meta_score(signal)

    th = get_threshold(regime)

    # 🔥 BYPASS nếu chưa có data

    if is_cold_start():

        return True, score, wr, conf

    if score < th:

        return False, score, wr, conf

    return True, score, wr, conf
