import numpy as np
import pandas as pd
import pickle
import os
import time

# 🔥 SAFE IMPORT (KHÔNG CÓ SKLEARN VẪN CHẠY)
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
# ENCODE SIGNAL
# =========================
def encode_signal(signal):

    regime_map = {"AGGRESSIVE": 1, "NEUTRAL": 0, "DEFENSIVE": -1}
    type_map = {"breakout": 1, "pullback": 0, "unknown": -1}

    return np.array([
        signal["rr"],
        signal["score"],
        signal["correlation"],
        signal["volatility"],
        signal["liquidity"],
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
    y = 1 if result == 1 else 0

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

    model = LogisticRegression(max_iter=200)
    model.fit(X_scaled, y)

    save_model(model, scaler)

    print("✅ Meta model updated")


# =========================
# 🔥 FALLBACK LOGIC (NO SKLEARN)
# =========================
def fallback_prob(signal):
    """
    Khi không có model → dùng heuristic thông minh
    """

    score = 0

    # RR cao → tốt
    score += (signal["rr"] - 1.5) * 0.3

    # entry score mạnh
    score += signal["score"] * 0.15

    # volatility tốt
    score += signal["volatility"] * 5

    # correlation thấp tốt hơn (tránh market risk)
    score -= abs(signal["correlation"]) * 0.2

    # regime boost
    if signal["regime"] == "AGGRESSIVE":
        score += 0.3

    # sigmoid squash
    prob = 1 / (1 + np.exp(-score))

    return float(np.clip(prob, 0.3, 0.8))  # tránh overconfidence


# =========================
# PREDICT
# =========================
def meta_filter_v6(signal):

    model, scaler = load_model()

    # 🔥 nếu chưa có model → dùng fallback
    if model is None or not SKLEARN_AVAILABLE:
        return fallback_prob(signal)

    try:
        x = encode_signal(signal).reshape(1, -1)
        x_scaled = scaler.transform(x)

        prob = float(model.predict_proba(x_scaled)[0][1])

        # clamp tránh overfit
        return float(np.clip(prob, 0.2, 0.9))

    except:
        return fallback_prob(signal)


# =========================
# FINAL SAVE
# =========================
def save_meta():
    train_meta_model()
