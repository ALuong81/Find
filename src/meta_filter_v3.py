import numpy as np
import json

MODEL_FILE = "meta_model.json"

# =========================
# INIT
# =========================
FEATURE_SIZE = 5
LR = 0.05

# weights init
weights = np.zeros(FEATURE_SIZE)


# =========================
# LOAD / SAVE
# =========================
def save_model():
    try:
        with open(MODEL_FILE, "w") as f:
            json.dump(weights.tolist(), f)
    except:
        pass


def load_model():
    global weights
    try:
        with open(MODEL_FILE, "r") as f:
            weights = np.array(json.load(f))
        print("✅ META V3 MODEL LOADED")
    except:
        print("⚠️ INIT NEW MODEL")


load_model()


# =========================
# FEATURE BUILDER
# =========================
def build_features(signal):

    rr = signal.get("rr", 1)
    mtf = signal.get("mtf_score", 0)
    regime = signal.get("regime", "NEUTRAL")
    type_ = signal.get("type", "UNKNOWN")

    # normalize
    rr_norm = np.tanh(rr / 3)
    mtf_norm = np.tanh(mtf)

    regime_map = {
        "AGGRESSIVE": 1,
        "NEUTRAL": 0,
        "DEFENSIVE": -1
    }

    regime_score = regime_map.get(regime, 0)

    type_map = {
        "EARLY_BREAKOUT": 1.0,
        "PRE": 0.8,
        "EARLY": 0.6,
        "STRONG": 0.5,
        "PULLBACK": 0.4
    }

    type_score = type_map.get(type_, 0.5)

    # placeholder future feature
    vol_score = 0.5

    return np.array([
        rr_norm,
        mtf_norm,
        regime_score,
        type_score,
        vol_score
    ])


# =========================
# SIGMOID
# =========================
def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# =========================
# PREDICT
# =========================
def predict(signal):

    X = build_features(signal)

    z = np.dot(weights, X)
    prob = sigmoid(z)

    return prob


# =========================
# UPDATE (LEARNING)
# =========================
def update_model(signal, result):

    global weights

    X = build_features(signal)
    pred = predict(signal)

    # convert result: win=1, loss=0
    y = 1 if result == 1 else 0

    error = y - pred

    # gradient update
    weights += LR * error * X

    save_model()


# =========================
# FILTER
# =========================
def meta_filter_v3(signal):

    prob = predict(signal)

    regime = signal.get("regime", "NEUTRAL")

    # dynamic threshold
    if regime == "AGGRESSIVE":
        th = 0.5
    elif regime == "NEUTRAL":
        th = 0.55
    else:
        th = 0.6

    if prob < th:
        return False, prob

    return True, prob
