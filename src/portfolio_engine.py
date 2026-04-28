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

        if np.isnan(corr):
            return 0

        return corr

    except:
        return 0


# =========================
# META SCALE (🔥 NEW)
# =========================
def meta_scale(signal):

    # ensemble probability
    prob = signal.get("meta_prob", 0.5)

    # agreement giữa models
    v2 = signal.get("meta_v2", 0.5)
    v3 = signal.get("meta_v3", 0.5)

    confidence = 1 - abs(v2 - v3)

    # final scale
    return (0.6 + prob) * (0.7 + 0.6 * confidence)


# =========================
# MAIN OPTIMIZER V4
# =========================
def optimize_portfolio(signals, data_map, equity):

    if not signals:
        return []

    # =========================
    # 🔥 SORT (AI PRIORITY)
    # =========================
    signals = sorted(
        signals,
        key=lambda x: (
            x.get("score", 0) * 0.6 +
            x.get("meta_prob", 0.5) * 0.4
        ),
        reverse=True
    )

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
        # 🔥 META SCALE (NEW)
        # =========================
        m_scale = meta_scale(s)

        # =========================
        # CORRELATION
        # =========================
        reduce_factor = 1.0
        corr_penalty = 0

        for f in final:

            df2 = data_map.get(f["symbol"])

            if df2 is None or len(df2) < MIN_DATA:
                continue

            corr = compute_correlation(df1, df2)

            if corr > CORR_THRESHOLD:
                reduce_factor *= 0.5
                corr_penalty += (corr - CORR_THRESHOLD)

        # =========================
        # APPLY SIZE
        # =========================
        adj_size = s["size"] * reduce_factor * m_scale

        risk = adj_size * abs(s["entry"] - s["sl"]) / equity

        # =========================
        # 🔥 RISK PRIORITY FILTER
        # =========================
        if total_risk + risk > MAX_TOTAL_RISK:

            # nếu trade rất tốt → cho vào 1 phần
            if s.get("meta_prob", 0.5) > 0.65:
                remain = MAX_TOTAL_RISK - total_risk
                if remain <= 0:
                    continue

                scale = remain / risk
                adj_size *= scale
                risk = remain
            else:
                continue

        # =========================
        # UPDATE SIGNAL
        # =========================
        s["size"] = round(adj_size, 2)
        s["risk_pct"] = round(risk, 4)
        s["meta_scale"] = round(m_scale, 3)
        s["corr_penalty"] = round(corr_penalty, 3)

        final.append(s)

        # =========================
        # UPDATE STATE
        # =========================
        sector_count[sector] = sector_count.get(sector, 0) + 1
        total_risk += risk

    return final
