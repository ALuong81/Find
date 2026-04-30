import numpy as np


# =========================
# UTIL
# =========================
def compute_atr(df, period=14):
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr = np.maximum(
        high - low,
        np.maximum(
            abs(high - close.shift()),
            abs(low - close.shift())
        )
    )
    atr = tr.rolling(period).mean().iloc[-1]

    if np.isnan(atr) or atr <= 0:
        # fallback nhỏ nhưng không méo RR
        atr = (high - low).rolling(20).mean().iloc[-1]
        if np.isnan(atr) or atr <= 0:
            atr = close.iloc[-1] * 0.02

    return float(atr)


def compute_rsi(close, period=14):
    delta = close.diff()
    up = np.maximum(delta, 0.0)
    down = np.maximum(-delta, 0.0)

    ma_up = up.rolling(period).mean()
    ma_down = down.rolling(period).mean()

    rs = ma_up / (ma_down + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])


# =========================
# ENTRY SCORE ENGINE (V6)
# =========================
def entry_score(df, df_h1=None):
    """
    V6: Trend + Structure + Breakout Quality + Volume + Pullback Entry (anti-FOMO)
    Trả về:
        entry, sl, tp1, tp2, score, type, volatility, liquidity, correlation
    """

    try:
        if df is None or len(df) < 60:
            return None

        close = df["close"]
        high = df["high"]
        low = df["low"]
        vol = df["volume"] if "volume" in df else None

        price = float(close.iloc[-1])

        # =========================
        # TREND FILTER (không trade downtrend)
        # =========================
        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]

        if np.isnan(ma20) or np.isnan(ma50) or ma20 <= ma50:
            return None

        # =========================
        # STRUCTURE (HH + HL)
        # =========================
        prev_highs = high.iloc[-6:-1]
        prev_lows = low.iloc[-6:-1]

        if len(prev_highs) < 5:
            return None

        hh = high.iloc[-1] > prev_highs.max()
        hl = low.iloc[-1] > prev_lows.min()

        if not (hh and hl):
            return None

        # =========================
        # BREAKOUT (so với 10 phiên trước)
        # =========================
        prior_high_10 = high.iloc[-11:-1].max()
        breakout = price > prior_high_10

        if not breakout:
            return None

        # =========================
        # ATR chuẩn (không dùng %)
        # =========================
        atr = compute_atr(df, 14)

        # =========================
        # VOLUME CONFIRM
        # =========================
        vol_score = 1.0
        if vol is not None and len(vol) >= 20:
            vol_mean = vol.rolling(20).mean().iloc[-1]
            vol_now = vol.iloc[-1]
            if vol_mean > 0:
                vol_score = vol_now / (vol_mean + 1e-9)

        if vol_score < 1.2:
            return None

        # =========================
        # ANTI SPIKE (tránh mua nến quá dài)
        # =========================
        candle_range = high.iloc[-1] - low.iloc[-1]
        if candle_range > atr * 2.5:
            return None

        # =========================
        # RSI FILTER (tránh quá mua)
        # =========================
        rsi = compute_rsi(close)
        if rsi > 75:
            return None

        # =========================
        # ENTRY (pullback nhẹ dưới close)
        # =========================
        # không mua đỉnh: đặt thấp hơn close 0.3%–0.7%
        entry = price * 0.995

        # =========================
        # STOP LOSS (dưới swing low gần nhất)
        # =========================
        swing_low_5 = low.iloc[-5:].min()
        sl = min(swing_low_5, entry - atr * 1.5)

        risk = entry - sl
        if risk <= 0:
            return None

        # =========================
        # TAKE PROFIT (dynamic)
        # =========================
        tp1 = entry + atr * 2.2
        tp2 = entry + atr * 3.5

        reward = tp1 - entry
        rr = reward / (risk + 1e-9)

        # RR tối thiểu để có edge
        if rr < 1.3:
            return None

        # =========================
        # SCORE (chất lượng setup)
        # =========================
        trend_strength = (price / (ma20 + 1e-9)) - 1.0  # >0 là tốt
        momentum = np.tanh((close.pct_change(3).iloc[-1] +
                            close.pct_change(5).iloc[-1]) * 5)

        # ưu tiên breakout có volume + trend rõ + không quá nóng
        score = (
            2.0 * np.tanh(trend_strength * 10) +
            1.5 * np.tanh(vol_score - 1.0) +
            1.2 * (1.0 if hh else 0.0) +
            1.0 * momentum +
            0.5 * np.tanh((70 - rsi) / 20.0)  # RSI càng thấp (nhưng vẫn >50) càng tốt
        )

        # normalize
        score = float(score * (1 + np.tanh(score / 3.0)))

        # =========================
        # EXTRA FEATURES (cho META)
        # =========================
        volatility = float(atr / (price + 1e-9))
        liquidity = float(np.tanh((vol_score - 1.0))) if vol is not None else 0.0
        correlation = 0.0  # set bên ngoài nếu có RS

        return {
            "entry": float(entry),
            "sl": float(sl),
            "tp1": float(tp1),
            "tp2": float(tp2),
            "score": float(score),
            "type": "BREAKOUT_PULLBACK_V6",
            "volatility": volatility,
            "liquidity": liquidity,
            "correlation": correlation
        }

    except Exception as e:
        print(f"[ENTRY V6 ERROR] {str(e)}")
        return None
