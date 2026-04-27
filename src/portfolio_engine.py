import numpy as np


MAX_PER_SECTOR = 2
MAX_TOTAL_RISK = 0.06
CORR_THRESHOLD = 0.7


def compute_correlation(df1, df2):

    try:
        r1 = df1["close"].pct_change().dropna()
        r2 = df2["close"].pct_change().dropna()

        min_len = min(len(r1), len(r2))
        if min_len < 20:
            return 0

        corr = np.corrcoef(r1[-min_len:], r2[-min_len:])[0, 1]
        return corr

    except:
        return 0


def optimize_portfolio(signals, data_map, equity):

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

        # =========================
        # CORRELATION CHECK
        # =========================
        reduce_factor = 1.0

        for f in final:

            df1 = data_map.get(symbol)
            df2 = data_map.get(f["symbol"])

            if df1 is None or df2 is None:
                continue

            corr = compute_correlation(df1, df2)

            if corr > CORR_THRESHOLD:
                reduce_factor *= 0.5  # 🔥 giảm size

        # =========================
        # APPLY REDUCTION
        # =========================
        size = s["size"] * reduce_factor

        risk = size * abs(s["entry"] - s["sl"]) / equity

        # =========================
        # TOTAL RISK LIMIT
        # =========================
        if total_risk + risk > MAX_TOTAL_RISK:
            continue

        s["size"] = round(size, 2)
        s["risk_pct"] = round(risk, 4)

        final.append(s)

        sector_count[sector] = sector_count.get(sector, 0) + 1
        total_risk += risk

    return final
