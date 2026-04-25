import pandas as pd


def accumulation_days(df):
    """
    Đếm số ngày tích lũy (giá sideway + vol cao)
    """
    if len(df) < 20:
        return 0

    recent = df.tail(10)

    price_range = recent["high"].max() - recent["low"].min()
    avg_price = recent["close"].mean()

    vol = recent["volume"]
    vol_avg = df["volume"].rolling(20).mean().iloc[-1]

    # sideway + vol cao
    if avg_price == 0:
        return 0

    if price_range / avg_price < 0.05:
        return (vol > vol_avg * 1.2).sum()

    return 0


def absorption_score(df):
    """
    Tổ chức hấp thụ: vol lớn nhưng giá không giảm
    """
    if len(df) < 5:
        return 0

    score = 0

    for i in range(-5, 0):
        vol = df["volume"].iloc[i]
        vol_avg = df["volume"].rolling(20).mean().iloc[i]
        close = df["close"].iloc[i]
        prev = df["close"].iloc[i - 1]

        if vol > vol_avg * 1.3 and close >= prev:
            score += 1

    return score


def expansion_quality(df):
    """
    Breakout có chất lượng hay chỉ là fake
    """
    if len(df) < 20:
        return 0

    high = df["high"].tail(20).max()
    close = df["close"].iloc[-1]

    vol = df["volume"]
    vol_avg = vol.rolling(20).mean()

    if close >= high * 0.95:
        if vol.iloc[-1] > vol_avg.iloc[-1] * 1.5:
            return 1   # strong breakout
        elif vol.iloc[-1] > vol_avg.iloc[-1]:
            return 0.5 # ok breakout

    return 0


def institutional_flow_score(df):
    """
    Tổng hợp dòng tiền tổ chức
    """

    acc = accumulation_days(df)
    absb = absorption_score(df)
    exp = expansion_quality(df)

    score = (
        acc * 0.8 +
        absb * 1.2 +
        exp * 1.5
    )

    return score
