import os

from symbol_loader import load_symbols
from data_loader import load_stock_data, load_index

from market_ranking import market_ranking
from sector_ranking import sector_ranking

from fake_breakout import detect_fake_breakout
from entry import validate_entry
from risk import market_risk

from sector_history import save_sector_history
from sector_trend import detect_emerging_sectors
from sector_heatmap import build_heatmap

from alert import send, send_image
from logger import log_info, log_error


def main():

    log_info("=== START RUN ===")

    try:
        # =========================
        # 1. LOAD SYMBOLS
        # =========================
        df_symbols = load_symbols()

        if df_symbols is None or df_symbols.empty:
            log_error("No symbols loaded")
            return

        # =========================
        # 2. MARKET RANKING
        # =========================
        market = market_ranking(df_symbols, load_stock_data)

        if not market:
            log_error("Market ranking empty")
            return

        top_stocks = market[:20]
        top_sectors = sector_ranking(market)[:5]

        # =========================
        # 3. SAVE & VISUALIZE SECTOR FLOW
        # =========================
        save_sector_history(top_sectors)

        img = build_heatmap()
        if img:
            send_image(img)

        emerging = detect_emerging_sectors()

        # =========================
        # 4. MARKET RISK CHECK
        # =========================
        # df_index = load_stock_data("VNINDEX")
        df_index = load_index()
        risk = market_risk(df_index)

        if risk >= 3:
            send("🚨 MARKET RISK HIGH - STOP TRADING")
            log_info("Market risk high - exit")
            return

        # =========================
        # 5. SEND MARKET OVERVIEW
        # =========================
        msg = "📊 MARKET OVERVIEW\n\n"

        msg += "🔥 TOP SECTORS:\n"
        for s, sc in top_sectors:
            msg += f"{s}: {round(sc,3)}\n"

        msg += "\n💪 TOP STOCKS:\n"
        for s in top_stocks[:10]:
            msg += f"{s['symbol']} | {round(s['score'],3)}\n"

        msg += f"\n⚠️ Risk Level: {risk}"

        if emerging:
            msg += "\n\n🚀 Emerging Sectors:\n"
            for s, sc in emerging[:3]:
                msg += f"{s}: {round(sc,3)}\n"

        send(msg)

        # =========================
        # 6. SCAN ENTRY
        # =========================
        for item in top_stocks:

            symbol = item["symbol"]

            try:
                df = load_stock_data(symbol)

                # ❌ bỏ fake breakout
                if detect_fake_breakout(df):
                    continue

                ok, fibo = validate_entry(df)

                if ok:
                    trade_msg = f"""
📈 TRADE SETUP

{symbol}

Entry: {round(fibo["entry"],2)}
SL: {round(fibo["sl"],2)}
TP1: {round(fibo["tp1"],2)}
TP2: {round(fibo["tp2"],2)}

Score: {round(item["score"],3)}
"""

                    send(trade_msg)

                    log_info(f"Signal: {symbol}")

            except Exception as e:
                log_error(f"{symbol} error: {str(e)}")
                continue

    except Exception as e:
        log_error(f"MAIN ERROR: {str(e)}")
        send(f"❌ SYSTEM ERROR: {str(e)}")

    log_info("=== END RUN ===")


if __name__ == "__main__":
    main()
