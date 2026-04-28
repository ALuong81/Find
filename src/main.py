from portfolio_engine import optimize_portfolio
from symbol_loader import load_symbols
from data_loader import load_stock_data, load_index, load_stock_data_h1

from smart_money import sector_money_flow, pick_leaders
from sector_rotation import sector_rotation
from relative_strength import relative_strength
from entry import validate_entry
from voe import voe_score

from institutional import institutional_score
from institutional_flow import institutional_flow_score
from money_flow import money_flow_score
from flow_timeline import flow_timeline

from mtf_confirm import mtf_confirm
from tracker import log_trade

from leader_score import compute_leader_score
from risk_engine import position_size

# 🔥 NEW
from meta_filter_v4 import meta_filter_v4
from meta_filter_v3_5 import update_model

import os
import requests
import numpy as np


# =========================
# TELEGRAM
# =========================
def send_telegram(msg):

    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("⚠️ TELEGRAM NOT CONFIG")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": chat_id,
            "text": msg
        })
    except Exception as e:
        print("❌ TELEGRAM ERROR:", str(e))


# =========================
# MARKET REGIME
# =========================
def market_regime(df_index):

    try:
        close = df_index["close"]

        ret_5 = close.pct_change(5).iloc[-1]
        ret_20 = close.pct_change(20).iloc[-1]
        vol = close.pct_change().rolling(20).std().iloc[-1]

        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]

        trend = 1 if ma20 > ma50 else -1

        score = (
            ret_5 * 2 +
            ret_20 * 1.5 -
            vol * 2 +
            trend
        )

        score = np.tanh(score * 3)

        if score > 0.3:
            return "AGGRESSIVE", score
        elif score > -0.3:
            return "NEUTRAL", score
        else:
            return "DEFENSIVE", score

    except:
        return "DEFENSIVE", -1


# =========================
# MAIN
# =========================
def main():

    print("🚀 START BOT V4")

    df_symbols = load_symbols()
    df_index = load_index()

    mode, m_score = market_regime(df_index)
    print("⚙️ MODE:", mode, "| score:", round(m_score, 3))

    # =========================
    # SYMBOL → SECTOR MAP
    # =========================
    symbol_to_sector = {
        row["symbol"]: row["sector"]
        for _, row in df_symbols.iterrows()
    }

    # =========================
    # SECTOR
    # =========================
    sector_df = sector_money_flow(df_symbols)
    sector_df = sector_rotation(sector_df)

    top_sectors = sector_df.head(3)

    # =========================
    # RAW LEADERS
    # =========================
    leaders = []

    for _, row in top_sectors.iterrows():
        stocks = pick_leaders(df_symbols, row["sector"])
        leaders += stocks["symbol"].tolist()

    leaders = list(set(leaders))

    # =========================
    # SCORING
    # =========================
    scored = []

    for symbol in leaders:

        try:
            df = load_stock_data(symbol)

            if df is None or len(df) < 30:
                continue

            df["value"] = df["close"] * df["volume"]
            liq_score = np.tanh(df["value"].rolling(20).mean().iloc[-1] / 1e9)

            rs = relative_strength(df, df_index)
            voe = voe_score(df, df_index)
            inst = institutional_score(df)
            inst_flow = institutional_flow_score(df)
            mf = money_flow_score(df)
            flow_acc = flow_timeline(df)

            sector = symbol_to_sector.get(symbol)
            sector_row = sector_df[sector_df["sector"] == sector]

            if sector_row.empty:
                continue

            sector_row = sector_row.iloc[0]

            leader_score = compute_leader_score(
                rs=rs,
                rotation_score=sector_row["rotation_score"],
                rs_sector=rs - sector_row.get("sector_return", 0),
                inst=inst,
                inst_flow=inst_flow,
                mf=mf,
                flow_timeline=flow_acc,
                voe=voe
            )

            leader_score *= (0.7 + 0.6 * liq_score)

            scored.append((symbol, leader_score))

        except Exception as e:
            print(symbol, "SCORING ERROR:", str(e))

    scored = sorted(scored, key=lambda x: x[1], reverse=True)
    leaders = [s[0] for s in scored[:12]]

    # =========================
    # PRELOAD (FIX)
    # =========================
    data_map = {}
    for s in leaders:
        df = load_stock_data(s)
        if df is not None:
            data_map[s] = df

    # =========================
    # ENTRY
    # =========================
    signals = []
    equity = 100000
    peak_equity = equity

    for symbol in leaders:

        try:
            df = data_map.get(symbol)
            if df is None:
                continue

            ok, f = validate_entry(df, symbol, regime=mode)
            if not ok:
                continue

            risk = f["entry"] - f["sl"]
            reward = f["tp1"] - f["entry"]

            if risk <= 0:
                continue

            rr = reward / risk
            if rr < 1.0:
                continue

            # MTF
            try:
                df_h1 = load_stock_data_h1(symbol)
                mtf_score = mtf_confirm(df, df_h1) if df_h1 is not None else 0
            except:
                mtf_score = 0

            system_score = next((x[1] for x in scored if x[0] == symbol), 0)

            final_score = rr * (1 + system_score * 0.1) * (1 + mtf_score * 0.3)

            sector = symbol_to_sector.get(symbol, "UNKNOWN")

            signal = {
                "symbol": symbol,
                "sector": sector,
                "entry": f["entry"],
                "sl": f["sl"],
                "tp1": f["tp1"],
                "tp2": f["tp2"],
                "rr": rr,
                "type": f["type"],
                "score": final_score,
                "mtf_score": round(mtf_score, 2),
                "regime": mode   # 🔥 CRITICAL
            }

            # =========================
            # 🔥 META FILTER V4
            # =========================
            ok_meta, prob, p2, p3 = meta_filter_v4(signal)

            if not ok_meta:
                continue

            # =========================
            # 🔥 POSITION SIZE
            # =========================
            size = position_size(
                equity=equity,
                signal=signal,
                regime=mode,
                df=df,
                peak_equity=peak_equity
            )

            # 🔥 scale theo AI confidence
            size *= (0.7 + prob)

            risk_pct = (size * abs(signal["entry"] - signal["sl"])) / equity

            signal.update({
                "size": round(size, 2),
                "risk_pct": round(risk_pct, 4),
                "meta_prob": round(prob, 3),
                "meta_v2": round(p2, 3),
                "meta_v3": round(p3, 3)
            })

            signals.append(signal)

            # 🔥 LEARNING
            update_model(signal, result=1, equity=equity, peak_equity=peak_equity)

            log_trade(symbol, f["entry"], f["sl"], f["tp1"])

            print(f"{symbol} ✅ score={round(final_score,2)} size={round(size,2)}")

        except Exception as e:
            print(symbol, "ERROR:", str(e))

    # =========================
    # PORTFOLIO
    # =========================
    signals = sorted(signals, key=lambda x: x["score"], reverse=True)
    signals = optimize_portfolio(signals, data_map, equity)

    print("\nTOTAL SIGNAL:", len(signals))

    if signals:

        msg = f"🔥 V4 SIGNALS | MODE: {mode}\n\n"

        for s in signals[:10]:
            msg += (
                f"{s['symbol']} ({s['type']})\n"
                f"Entry: {round(s['entry'],2)}\n"
                f"SL: {round(s['sl'],2)}\n"
                f"RR: {round(s['rr'],2)}\n"
                f"AI Prob: {s['meta_prob']}\n"
                f"Size: {s['size']}\n"
                f"Risk: {s['risk_pct']*100:.2f}%\n\n"
            )

        send_telegram(msg)

    else:
        print("⚠️ NO SIGNAL")


if __name__ == "__main__":
    main()
