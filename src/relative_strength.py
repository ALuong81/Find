import numpy as np
import pandas as pd


# =========================
# EMA SMOOTH
# =========================
def ema_smooth(series, span=5):
    return series.ewm(span=span, adjust=False).mean().iloc[-1]


# =========================
# SAFE RETURN
# =========================
def safe_return(close, period):
    if len(close) < period + 1:
        return 0
    return close.pct_change(period).iloc[-1]


# =========================
# MAIN RS (V4)
# =========================
def relative_strength(df_stock, df_index):

    try:
        if df_stock is None or df_index is None:
            return 0

        if len(df_stock) < 30 or len(df_index) < 30:
            return 0

        stock_close = df_stock["close"]
        index_close = df_index["close"]

        # =========================
        # MULTI HORIZON RETURN
        # =========================
        rs_5 = safe_return(stock_close, 5) - safe_return(index_close, 5)
        rs_10 = safe_return(stock_close, 10) - safe_return(index_close, 10)
        rs_20 = safe_return(stock_close, 20) - safe_return(index_close, 20)

        # =========================
        # BUILD SERIES (FOR SMOOTH)
        # =========================
        rs_series = []

        for i in range(25, len(df_stock)):
            try:
                s = df_stock["close"].iloc[:i]
                idx = df_index["close"].iloc[:i]

                r5 = safe_return(s, 5) - safe_return(idx, 5)
                r10 = safe_return(s, 10) - safe_return(idx, 10)
                r20 = safe_return(s, 20) - safe_return(idx, 20)

                rs_series.append(
                    r5 * 0.4 +
                    r10 * 0.3 +
                    r20 * 0.3
                )

            except:
                continue

        if len(rs_series) < 5:
            return 0

        rs_series = pd.Series(rs_series)

        # =========================
        # EMA SMOOTH
        # =========================
        rs_smooth = ema_smooth(rs_series, span=5)

        # =========================
        # FINAL SCORE (NONLINEAR SCALE)
        # =========================
        rs_final = np.tanh(rs_smooth * 5)

        return rs_final

    except Exception as e:
        print("RS ERROR:", str(e))
        return 0
