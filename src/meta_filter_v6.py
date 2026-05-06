import numpy as np
import pandas as pd
import pickle
import os
import time

# =========================
# SAFE IMPORT
# =========================
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except:
    SKLEARN_AVAILABLE = False
    print("⚠️ sklearn not available → fallback mode")

MODEL_PATH = "meta_model.pkl"
DATA_PATH = "meta_data.csv"

COLUMNS = [
    "rr", "score", "correlation", "volatility",
    "liquidity", "regime", "type", "label"
]


# =========================
# INIT FILE
# =========================
def ensure_data_file():
    if not os.path.exists(DATA_PATH):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(DATA_PATH, index=False)


# =========================
# 🔥 ENCODE SIGNAL (FIX FULL)
# =========================
def encode_signal(signal):

    regime_map = {"AGGRESSIVE": 1, "NEUTRAL": 0, "DEFENSIVE": -1}

    # 🔥 FIX: thêm đầy đủ type mới
    type_map = {
        "breakout": 1,
        "early_break": 0.5,
        "weak_break": 0.2,
        "pullback": 0,
        "unknown": -1
    }

    return np.array([
        signal["rr"],

        # 🔥 FIX: scale score ổn định hơn
        signal["score"] / 10,

        # correlation giữ nguyên
        signal["correlation"],

        # 🔥 FIX: scale volatility hợp lý hơn
        signal["volatility"] * 100,

        # 🔥 FIX: tránh log(0)
        np.log1p(max(signal["liquidity"], 1)),

        regime_map.get(signal["regime"], 0),

        type_map.get(signal["type"], 0)
    ])


# =========================
# LOAD / SAVE MODEL
# =========================
def load_model():
    if not os.path.exists(MODEL_PATH):
        return None, None
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def save_model(model, scaler):
    with open(MODEL_PATH, "wb") as f:
        pickle.dump((model, scaler), f)


# =========================
# SAFE APPEND
# =========================
def safe_append(df_row, max_retry=3):

    for _ in range(max_retry):
        try:
            df_row.to_csv(DATA_PATH, mode="a", header=False, index=False)
            return
        except PermissionError:
            time.sleep(0.2)

    print("⚠️ Cannot write meta_data.csv (file locked)")


# =========================
# UPDATE DATA
# =========================
def update_meta_v6(signal, result):

    ensure_data_file()

    X = encode_signal(signal)

    # 🔥 FIX: BE (-0.5) không nên coi là loss hoàn toàn
    if result == 1:
        y = 1
    elif result == -1:
        y = 0
    else:
        y = 0.3   # 🔥 neutral outcome

    row = pd.DataFrame([np.append(X, y)], columns=COLUMNS)

    safe_append(row)


# =========================
# TRAIN MODEL
# =========================
def train_meta_model():

    if not SKLEARN_AVAILABLE:
        print("⚠️ skip training (no sklearn)")
        return

    ensure_data_file()

    df = pd.read_csv(DATA_PATH)

    if len(df) < 200:
        print("⚠️ not enough data to train meta")
        return

    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=300)
    model.fit(X_scaled, y)

    save_model(model, scaler)

    print("✅ Meta model updated")


# =========================
# 🔥 FALLBACK LOGIC (FIX EDGE)
# =========================
def fallback_prob(signal):

    score = 0

    # =========================
    # RR (giảm bias)
    # =========================
    score += (signal["rr"] - 1.5) * 0.12

    # =========================
    # ENTRY QUALITY
    # =========================
    score += signal["score"] * 0.07

    # =========================
    # VOLATILITY SWEET SPOT
    # =========================
    vol = signal["volatility"]
    score += -abs(vol - 0.02) * 18

    # =========================
    # CORRELATION (giảm penalty)
    # =========================
    score -= abs(signal["correlation"]) * 0.25

    # =========================
    # REGIME
    # =========================
    if signal["regime"] == "AGGRESSIVE":
        score += 0.25
    elif signal["regime"] == "DEFENSIVE":
        score -= 0.3

    # =========================
    # TYPE LOGIC (🔥 FIX QUAN TRỌNG)
    # =========================
    if signal["type"] == "early_break":
        score -= 0.25
    elif signal["type"] == "weak_break":
        score -= 0.1
    elif signal["type"] == "breakout":
        score += 0.15

    # =========================
    # LIQUIDITY
    # =========================
    score += np.log1p(signal["liquidity"]) * 0.04

    # =========================
    # SIGMOID
    # =========================
    prob = 1 / (1 + np.exp(-score))

    # 🔥 FIX: realistic range hơn
    return float(np.clip(prob, 0.45, 0.7))


# =========================
# PREDICT
# =========================
def meta_filter_v6(signal):

    model, scaler = load_model()

    if model is None or not SKLEARN_AVAILABLE:
        return fallback_prob(signal)

    try:
        x = encode_signal(signal).reshape(1, -1)
        x_scaled = scaler.transform(x)

        prob = float(model.predict_proba(x_scaled)[0][1])

        return float(np.clip(prob, 0.4, 0.75))

    except:
        return fallback_prob(signal)


# =========================
# FINAL SAVE
# =========================
def save_meta():
    train_meta_model()
