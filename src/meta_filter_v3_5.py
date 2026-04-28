import numpy as np
import json
import os

MODEL_FILE = "meta_model_v3_5.json"

FEATURE_SIZE = 8
BASE_LR = 0.03
L2_REG = 0.001

MIN_SAMPLES = 30

# =========================
# INIT
# =========================
weights = np.zeros(FEATURE_SIZE)
bias = 0.0
sample_count = 0

_model_loaded = False   # 🔥 đảm bảo chỉ load 1 lần


# =========================
# FILE INIT (NEW)
# =========================
def init_model_file():

    if not os.path.exists(MODEL_FILE):
        try:
            with open(MODEL_FILE, "w") as f:
                json.dump({
                    "weights": weights.tolist(),
                    "bias": bias,
                    "sample_count": 0
                }, f)

            print("⚠️ CREATE NEW META MODEL FILE")

        except Exception as e:
            print("❌ INIT FILE ERROR:", str(e))


# =========================
# LOAD / SAVE
# =========================
def save_model():
    try:
        with open(MODEL_FILE, "w") as f:
            json.dump({
                "weights": weights.tolist(),
                "bias": bias,
                "sample_count": sample_count
            }, f)
    except Exception as e:
        print("❌ SAVE MODEL ERROR:", str(e))


def load_model():

    global weights, bias, sample_count, _model_loaded

    if _model_loaded:
        return

    init_model_file()   # 🔥 đảm bảo file tồn tại trước

    try:
        with open(MODEL_FILE, "r") as f:
            data = json.load(f)

            weights[:] = data.get("weights", weights)
            bias = data.get("bias", 0.0)
            sample_count = data.get("sample_count", 0)

        print(f"✅ META V3.5 LOADED | samples={sample_count}")

    except Exception as e:
        print("❌ LOAD MODEL ERROR:", str(e))

    _model_loaded = True   # 🔥 chỉ load 1 lần


# 🔥 KHÔNG auto load khi import
# load_model()  ❌ remove dòng này


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

    load_model()   # 🔥 đảm bảo load trước khi dùng

    X = build_features(signal)
    z = np.dot(weights, X) + bias
    prob = sigmoid(z)

    return prob


# =========================
# CONFIDENCE
# =========================
def confidence():

    if sample_count < MIN_SAMPLES:
        return 0.3

    return np.tanh(sample_count / 100)


# =========================
# LR
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
# UPDATE
# =========================
def update_model(signal, result, equity=1, peak_equity=1):

    global weights, bias, sample_count

    load_model()   # 🔥 đảm bảo load

    X = build_features(signal)
    pred = predict(signal)

    y = 1 if result == 1 else 0
    error = y - pred

    lr = get_learning_rate(equity, peak_equity)

    weights += lr * (error * X - L2_REG * weights)
    bias += lr * error

    weights = np.clip(weights, -3, 3)
    bias = np.clip(bias, -2, 2)

    sample_count += 1

    save_model()


# =========================
# THRESHOLD
# =========================
def get_threshold(signal):

    regime = signal.get("regime", "NEUTRAL")
    vol = signal.get("volatility", 0.2)

    base = 0.52

    if regime == "AGGRESSIVE":
        base -= 0.05
    elif regime == "DEFENSIVE":
        base += 0.03

    base += np.tanh(vol * 2) * 0.03

    return base


# =========================
# FILTER
# =========================
def meta_filter_v3_5(signal):

    prob = predict(signal)
    th = get_threshold(signal)
    conf = confidence()

    # 🔥 cold start
    if sample_count < MIN_SAMPLES:
        return True, prob

    # 🔥 low confidence
    if conf < 0.4:
        if prob > (th - 0.05):
            return True, prob
        else:
            return False, prob

    if prob < th:
        return False, prob

    return True, prob
