import numpy as np


# =========================
# CONFIG
# =========================
MAX_PER_SECTOR = 2
MAX_TOTAL_RISK = 0.06
CORR_THRESHOLD = 0.7
MIN_DATA = 20


# =========================
# CORRELATION
# =========================
def compute_correlation(df1, df2):

    try:
        r1 = df1["close"].pct_change().dropna()
        r2 = df2["close"].pct_change().dropna()

        min_len = min(len(r1), len(r2))

        if min_len < MIN_DATA:
            return 0

        r1 = r1[-min_len:]
        r2 = r2[-min_len:]

        corr = np.corrcoef(r1, r2)[0, 1]

        # tránh NaN
        if np.isnan(corr):
            return 0

        return corr

    except:
        return 0


# =========================
# MAIN OPTIMIZER
# =========================
def optimize_portfolio(signals, data_map, equity):

    if not signals:
        return []

    # =========================
    # SORT BY SCORE
    # =========================
    signals = sorted(signals, key=lambda x: x["score"], reverse=True)

    final = []
    sector_count = {}
    total_risk = 0

    for s in signals:

        symbol = s["symbol"]
        sector = s.get("sector", "UNKNOWN")

        # =========================
        # SECTOR LIMIT
        # =========================
        if sector_count.get(sector, 0) >= MAX_PER_SECTOR:
            continue

        df1 = data_map.get(symbol)

        if df1 is None or len(df1) < MIN_DATA:
            continue

        # =========================
        # CORRELATION ADJUST
        # =========================
        reduce_factor = 1.0

        for f in final:

            df2 = data_map.get(f["symbol"])

            if df2 is None or len(df2) < MIN_DATA:
                continue

            corr = compute_correlation(df1, df2)

            # 🔥 nếu tương quan cao → giảm size
            if corr > CORR_THRESHOLD:
                reduce_factor *= 0.5

        # =========================
        # APPLY SIZE REDUCTION
        # =========================
        adj_size = s["size"] * reduce_factor

        risk = adj_size * abs(s["entry"] - s["sl"]) / equity

        # =========================
        # TOTAL RISK LIMIT
        # =========================
        if total_risk + risk > MAX_TOTAL_RISK:
            continue

        # =========================
        # UPDATE SIGNAL
        # =========================
        s["size"] = round(adj_size, 2)
        s["risk_pct"] = round(risk, 4)

        final.append(s)

        # =========================
        # UPDATE STATE
        # =========================
        sector_count[sector] = sector_count.get(sector, 0) + 1
        total_risk += risk

    return final
