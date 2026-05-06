import numpy as np
import pandas as pd
import pickle
import os
import time

# =========================
# TRY IMPORT SKLEARN
# =========================
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score
    SKLEARN_AVAILABLE = True
except:
    SKLEARN_AVAILABLE = False
    print("⚠️ sklearn not available → fallback mode")

MODEL_PATH = "meta_model_v7.pkl"
DATA_PATH = "meta_data_v7.csv"

COLUMNS = [
    "rr", "score", "correlation", "volatility",
    "liquidity", "regime", "type",
    "trend_strength", "vol_ratio", "breakout_strength",
    "label"
]

# =========================
# INIT FILE
# =========================
def ensure_data_file():
    if not os.path.exists(DATA_PATH):
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_PATH, index=False)

# =========================
# ENCODE
# =========================
def encode_signal(signal):

    regime_map = {"AGGRESSIVE": 1, "NEUTRAL": 0, "DEFENSIVE": -1}
    type_map = {
        "breakout": 1,
        "early_break": 0.5,
        "unknown": 0
    }

    return np.array([
        signal["rr"],
        signal["score"],
        signal["correlation"],
        signal["volatility"],
        signal["liquidity"],
        regime_map.get(signal["regime"], 0),
        type_map.get(signal["type"], 0),
        signal.get("trend_strength", 0),
        signal.get("vol_ratio", 1),
        signal.get("breakout_strength", 0)
    ])

# =========================
# LOAD / SAVE
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
def safe_append(df_row):
    try:
        df_row.to_csv(DATA_PATH, mode="a", header=False, index=False)
    except:
        pass

# =========================
# UPDATE DATA
# =========================
def update_meta_v7(signal, result):

    ensure_data_file()

    X = encode_signal(signal)

    # label
    if result == 1:
        y = 1
    elif result == -1:
        y = 0
    else:
        y = 0.3   # BE → neutral

    row = pd.DataFrame([np.append(X, y)], columns=COLUMNS)
    safe_append(row)

# =========================
# TRAIN
# =========================
def train_meta_model():

    if not SKLEARN_AVAILABLE:
        print("⚠️ skip training (no sklearn)")
        return

    ensure_data_file()
    df = pd.read_csv(DATA_PATH)

    if len(df) < 300:
        print("⚠️ not enough data")
        return

    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=6,
        min_samples_leaf=5,
        random_state=42
    )

    model.fit(X_train, y_train)

    # evaluate
    prob = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, prob)

    print(f"✅ Meta v7 trained | AUC = {round(auc,3)}")

    save_model(model, scaler)

# =========================
# FALLBACK (SAFE)
# =========================
def fallback_prob(signal):

    score = 0

    score += signal["rr"] * 0.2
    score += signal["score"] * 0.1
    score += signal.get("trend_strength", 0) * 5
    score += signal.get("vol_ratio", 1) * 0.5

    if signal["regime"] == "AGGRESSIVE":
        score += 0.3

    prob = 1 / (1 + np.exp(-score))
    return float(np.clip(prob, 0.35, 0.75))

# =========================
# PREDICT
# =========================
def meta_filter_v7(signal):

    model, scaler = load_model()

    if model is None or not SKLEARN_AVAILABLE:
        return fallback_prob(signal)

    try:
        x = encode_signal(signal).reshape(1, -1)
        x_scaled = scaler.transform(x)

        prob = float(model.predict_proba(x_scaled)[0][1])

        return float(np.clip(prob, 0.25, 0.85))

    except:
        return fallback_prob(signal)

# =========================
# FINAL SAVE
# =========================
def save_meta():
    train_meta_model()
