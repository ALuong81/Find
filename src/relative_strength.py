import numpy as np
import pandas as pd


# =========================
# SAFE RETURN
# =========================
def safe_pct_change(series, period):
    if len(series) < period + 1:
        return pd.Series([0] * len(series))
    return series.pct_change(period)


# =========================
# MAIN RS V4 (VECTOR + SMOOTH)
# =========================
def relative_strength(df_stock, df_index):

    try:
        if df_stock is None or df_index is None:
            return 0.0

        if len(df_stock) < 30 or len(df_index) < 30:
            return 0.0

        # =========================
        # ALIGN DATA
        # =========================
        s = df_stock[["date", "close"]].copy()
        i = df_index[["date", "close"]].copy()

        s["date"] = pd.to_datetime(s["date"], errors="coerce")
        i["date"] = pd.to_datetime(i["date"], errors="coerce")

        df = pd.merge(s, i, on="date", suffixes=("_s", "_i"))
        df = df.dropna()

        if len(df) < 30:
            return 0.0

        close_s = df["close_s"]
        close_i = df["close_i"]

        # =========================
        # MULTI-HORIZON RS
        # =========================
        rs_5 = safe_pct_change(close_s, 5) - safe_pct_change(close_i, 5)
        rs_10 = safe_pct_change(close_s, 10) - safe_pct_change(close_i, 10)
        rs_20 = safe_pct_change(close_s, 20) - safe_pct_change(close_i, 20)

        # =========================
        # COMBINE (WEIGHTED)
        # =========================
        rs_raw = (
            rs_5 * 0.4 +
            rs_10 * 0.3 +
            rs_20 * 0.3
        )

        # =========================
        # SMOOTH (EMA)
        # =========================
        rs_smooth = rs_raw.ewm(span=5, adjust=False).mean()

        # =========================
        # VOLATILITY NORMALIZATION
        # =========================
        vol = close_s.pct_change().rolling(20).std()

        # tránh chia 0
        vol = vol.replace(0, np.nan).fillna(method="bfill").fillna(0.01)

        rs_vol_adj = rs_smooth / (vol * 5)

        # =========================
        # FINAL SCALE [-1 → +1]
        # =========================
        rs_final = np.tanh(rs_vol_adj.iloc[-1])

        return float(rs_final)

    except Exception as e:
        print("RS ERROR:", str(e))
        return 0.0
