import numpy as np
import pandas as pd


# =========================
# SAFE RETURN
# =========================
def safe_pct_change(series, period):
    if len(series) < period + 1:
        return pd.Series([0.0] * len(series), index=series.index)
    return series.pct_change(period)


# =========================
# MAIN RS V4 (FIXED + STABLE)
# =========================
def relative_strength(df_stock, df_index):

    try:
        if df_stock is None or df_index is None:
            return 0.0

        if len(df_stock) < 30 or len(df_index) < 30:
            return 0.0

        # =========================
        # ALIGN DATA (ROBUST)
        # =========================
        s = df_stock[["date", "close"]].copy()
        i = df_index[["date", "close"]].copy()

        s["date"] = pd.to_datetime(s["date"], errors="coerce")
        i["date"] = pd.to_datetime(i["date"], errors="coerce")

        df = pd.merge(s, i, on="date", suffixes=("_s", "_i"))
        df = df.dropna()

        if len(df) < 30:
            return 0.0

        close_s = df["close_s"].astype(float)
        close_i = df["close_i"].astype(float)

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

        # fill NaN sớm để tránh lan lỗi
        rs_raw = rs_raw.fillna(0.0)

        # =========================
        # SMOOTH (EMA)
        # =========================
        rs_smooth = rs_raw.ewm(span=5, adjust=False).mean()

        # =========================
        # VOLATILITY NORMALIZATION (FIX)
        # =========================
        vol = close_s.pct_change().rolling(20).std()

        # 🔥 FIX pandas 2.x + tránh NaN
        vol = vol.replace(0, np.nan)
        vol = vol.bfill().ffill()  # thay fillna(method=...)
        vol = vol.fillna(0.01)     # fallback cuối

        # tránh blow up
        vol = np.clip(vol, 0.005, None)

        rs_vol_adj = rs_smooth / (vol * 5)

        # =========================
        # FINAL SCALE [-1 → +1]
        # =========================
        val = rs_vol_adj.iloc[-1]

        if pd.isna(val) or np.isinf(val):
            return 0.0

        rs_final = np.tanh(val)

        return float(rs_final)

    except Exception as e:
        print("RS ERROR:", str(e))
        return 0.0
