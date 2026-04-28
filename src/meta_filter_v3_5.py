import numpy as np
import json

MODEL_FILE = "meta_model_v3_5.json"

FEATURE_SIZE = 8
BASE_LR = 0.03
L2_REG = 0.001

# =========================
# INIT
# =========================
weights = np.zeros(FEATURE_SIZE)
bias = 0.0

# =========================
# LOAD / SAVE
# =========================
def save_model():
    try:
        with open(MODEL_FILE, "w") as f:
            json.dump({
                "weights": weights.tolist(),
                "bias": bias
            }, f)
    except:
        pass


def load_model():
    global weights, bias
    try:
        with open(MODEL_FILE, "r") as f:
            data = json.load(f)
            weights[:] = data["weights"]
            bias = data["bias"]
        print("✅ META V3.5 LOADED")
    except:
        print("⚠️ INIT NEW MODEL")


load_model()


# =========================
# FEATURE ENGINEERING
# =========================
def build_features(signal):

    rr = signal.get("rr", 1)
    mtf = signal.get("mtf_score", 0)
    regime = signal.get("regime", "NEUTRAL")
    type_ = signal.get("type", "UNKNOWN")

    vol = signal.get("volatility", 0.2)
    corr = signal.get("correlation", 0)
    liq = signal.get("liquidity", 1)

    # =========================
    # NORMALIZATION
    # =========================
    rr_n = np.tanh(rr / 3)
    mtf_n = np.tanh(mtf)
    vol_n = np.tanh(vol * 5)
    corr_n = corr
    liq_n = np.tanh(liq)

    regime_map = {
        "AGGRESSIVE": 1,
        "NEUTRAL": 0,
        "DEFENSIVE": -1
    }

    regime_n = regime_map.get(regime, 0)

    type_map = {
        "EARLY_BREAKOUT": 1.0,
        "PRE": 0.8,
        "EARLY": 0.6,
        "STRONG": 0.5,
        "PULLBACK": 0.4
    }

    type_n = type_map.get(type_, 0.5)

    # interaction terms (🔥 rất quan trọng)
    rr_mtf = rr_n * mtf_n
    rr_regime = rr_n * regime_n

    return np.array([
        rr_n,
        mtf_n,
        regime_n,
        type_n,
        vol_n,
        corr_n,
        liq_n,
        rr_mtf + rr_regime
    ])


# =========================
# SIGMOID
# =========================
def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -10, 10)))


# =========================
# PREDICT
# =========================
def predict(signal):

    X = build_features(signal)

    z = np.dot(weights, X) + bias
    prob = sigmoid(z)

    return prob


# =========================
# ADAPTIVE LR
# =========================
def get_learning_rate(equity, peak_equity):

    if peak_equity <= 0:
        return BASE_LR

    dd = (peak_equity - equity) / peak_equity

    if dd < 0.05:
        return BASE_LR
    elif dd < 0.1:
        return BASE_LR * 0.7
    elif dd < 0.2:
        return BASE_LR * 0.4
    else:
        return BASE_LR * 0.2


# =========================
# UPDATE MODEL
# =========================
def update_model(signal, result, equity=1, peak_equity=1):

    global weights, bias

    X = build_features(signal)
    pred = predict(signal)

    y = 1 if result == 1 else 0

    error = y - pred

    lr = get_learning_rate(equity, peak_equity)

    # gradient descent + L2 regularization
    weights += lr * (error * X - L2_REG * weights)
    bias += lr * error

    # 🔥 stability clamp
    weights = np.clip(weights, -3, 3)
    bias = np.clip(bias, -2, 2)

    save_model()


# =========================
# DYNAMIC THRESHOLD
# =========================
def get_threshold(signal):

    regime = signal.get("regime", "NEUTRAL")
    vol = signal.get("volatility", 0.2)

    base = 0.55

    if regime == "AGGRESSIVE":
        base -= 0.05
    elif regime == "DEFENSIVE":
        base += 0.08

    # high vol → cần chắc hơn
    base += np.tanh(vol * 2) * 0.05

    return base


# =========================
# FILTER
# =========================
def meta_filter_v3_5(signal):

    prob = predict(signal)
    th = get_threshold(signal)

    if prob < th:
        return False, prob

    return True, prob
