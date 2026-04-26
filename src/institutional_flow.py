import pandas as pd


# =========================
# ACCUMULATION DAYS (SMOOTH)
# =========================
def accumulation_days(df):

    if len(df) < 20:
        return 0

    recent = df.tail(10)

    price_range = recent["high"].max() - recent["low"].min()
    avg_price = recent["close"].mean()

    if avg_price == 0:
        return 0

    vol = recent["volume"]
    vol_avg = df["volume"].rolling(20).mean().iloc[-1]

    # sideway + vol cao
    if price_range / avg_price < 0.06:  # 🔥 nới nhẹ
        score = (vol > vol_avg * 1.1).sum() / 10  # 🔥 normalize [0-1]
        return score

    return 0


# =========================
# ABSORPTION (KHÔNG TRẢ 0 CỨNG)
# =========================
def absorption_score(df):

    if len(df) < 5:
        return 0

    score = 0

    for i in range(-5, 0):
        vol = df["volume"].iloc[i]
        vol_avg = df["volume"].rolling(20).mean().iloc[i]
        close = df["close"].iloc[i]
        prev = df["close"].iloc[i - 1]

        if vol_avg == 0:
            continue

        # 🔥 nới điều kiện
        if vol > vol_avg * 1.2:
            if close >= prev:
                score += 1
            else:
                score += 0.3  # 🔥 không trả 0 → vẫn có hấp thụ nhẹ

    return score / 5  # 🔥 normalize


# =========================
# EXPANSION QUALITY (SOFT)
# =========================
def expansion_quality(df):

    if len(df) < 20:
        return 0

    high = df["high"].tail(20).max()
    close = df["close"].iloc[-1]

    vol = df["volume"]
    vol_avg = vol.rolling(20).mean()

    if vol_avg.iloc[-1] == 0:
        return 0

    # 🔥 nới điều kiện breakout
    if close >= high * 0.97:

        if vol.iloc[-1] > vol_avg.iloc[-1] * 1.4:
            return 1.0
        elif vol.iloc[-1] > vol_avg.iloc[-1] * 1.1:
            return 0.6
        else:
            return 0.3  # 🔥 vẫn cho điểm nhẹ

    return 0.2  # 🔥 tránh trả 0 hoàn toàn


# =========================
# MAIN SCORE (SCALED + SMOOTH)
# =========================
def institutional_flow_score(df):

    try:
        if df is None or len(df) < 30:
            return 0

        # =========================
        # RAW COMPONENT
        # =========================
        acc = accumulation_days(df)
        absb = absorption_score(df)
        exp = expansion_quality(df)

        raw_score = (
            acc * 1.0 +
            absb * 1.2 +
            exp * 1.5
        )

        # =========================
        # 🔥 EMA SMOOTH (QUAN TRỌNG)
        # =========================
        # tạo series giả để smooth
        temp = pd.Series([raw_score] * 5)
        smooth = temp.ewm(span=3).mean().iloc[-1]

        # =========================
        # 🔥 SCALE VỀ [-1 → +2]
        # =========================
        # clamp trước
        smooth = max(min(smooth, 3), -1)

        # scale mềm
        scaled = (smooth / 3) * 2  # ~ [-1 → +2]

        return round(scaled, 2)

    except Exception as e:
        print("FLOW SCORE ERROR:", str(e))
        return 0
