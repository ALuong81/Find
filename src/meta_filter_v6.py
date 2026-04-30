import numpy as np
import json
import os

MODEL_PATH = "meta_v6.json"

class MetaModel:

    def __init__(self):
        self.w = None
        self.lr = 0.01

    def init_weights(self, dim):
        self.w = np.zeros(dim)

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def predict(self, x):
        return self.sigmoid(np.dot(self.w, x))

    def update(self, x, y):
        pred = self.predict(x)
        grad = (pred - y) * x
        self.w -= self.lr * grad


model = MetaModel()


# =========================
# FEATURE ENGINEERING
# =========================
def build_features(signal):

    return np.array([
        signal["rr"],
        signal["score"],
        signal.get("correlation", 0),
        signal.get("volatility", 0),
        1 if signal["regime"] == "AGGRESSIVE" else 0,
        1 if signal["regime"] == "DEFENSIVE" else 0
    ])


# =========================
# LOAD / SAVE
# =========================
def load_model():
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "r") as f:
            model.w = np.array(json.load(f))
    else:
        model.init_weights(6)


def save_model():
    with open(MODEL_PATH, "w") as f:
        json.dump(model.w.tolist(), f)


# =========================
# MAIN FILTER
# =========================
def meta_filter_v6(signal):

    x = build_features(signal)

    if model.w is None:
        model.init_weights(len(x))

    prob = model.predict(x)

    return prob


# =========================
# UPDATE
# =========================
def update_meta_v6(signal, result):

    x = build_features(signal)

    y = 1 if result == 1 else 0

    model.update(x, y)
