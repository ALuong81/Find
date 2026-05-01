import numpy as np
import pandas as pd
import pickle
import os
import time

# =========================
# OPTIONAL SKLEARN
# =========================
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except:
    SKLEARN_AVAILABLE = False


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
    ], dtype=float)


# =========================
# LOAD / SAVE MODEL
# =========================
def load_model():
    if not os.path.exists(MODEL_PATH):
        return None, None
    try:
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    except:
        return None, None


def save_model(model, scaler):
    try:
        with open(MODEL_PATH, "wb") as f:
            pickle.dump((model, scaler), f)
    except:
        print("⚠️ Cannot save model")


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

    print("⚠️ Cannot write meta_data.csv (file may be open)")


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
        print("⚠️ sklearn not available → skip training")
        return

    ensure_data_file()

    try:
        df = pd.read_csv(DATA_PATH)
    except:
        print("⚠️ Cannot read meta_data.csv")
        return

    # chưa đủ data → không train
    if len(df) < 200:
        return

    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values

    try:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = LogisticRegression(max_iter=200)
        model.fit(X_scaled, y)

        save_model(model, scaler)

        print("Meta model updated")

    except Exception as e:
        print(f"⚠️ Training failed: {e}")


# =========================
# SIMPLE FALLBACK MODEL
# =========================
def fallback_score(signal):
    """
    Khi không có sklearn → dùng heuristic nhẹ
    """

    score = 0

    score += signal["rr"] * 0.2
    score += signal["score"] * 0.15
    score += signal["correlation"] * 0.1
    score += signal["volatility"] * 5
    score += signal["liquidity"] * 0.05

    if signal["regime"] == "AGGRESSIVE":
        score += 0.3

    if signal["type"] == "breakout":
        score += 0.2

    # squash về 0–1
    return float(1 / (1 + np.exp(-score)))


# =========================
# PREDICT
# =========================
def meta_filter_v6(signal):

    # ❌ không có sklearn → fallback
    if not SKLEARN_AVAILABLE:
        return fallback_score(signal)

    model, scaler = load_model()

    # ❌ chưa có model → fallback nhẹ
    if model is None or scaler is None:
        return fallback_score(signal)

    try:
        x = encode_signal(signal).reshape(1, -1)
        x_scaled = scaler.transform(x)

        return float(model.predict_proba(x_scaled)[0][1])

    except:
        return fallback_score(signal)


# =========================
# FINAL SAVE
# =========================
def save_meta():
    train_meta_model()
    
