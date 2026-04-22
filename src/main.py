import logging
logging.getLogger("vnstock").setLevel(logging.CRITICAL)

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
        # 1. load symbols
        df_symbols = load_symbols()

        if df_symbols.empty:
            log_error("No symbols")
            return

        # 2. ranking
        market = market_ranking(df_symbols, load_stock_data)

        if not market:
            log_error("Market empty")
            return

        top_stocks = market[:20]
        top_sectors = sector_ranking(market)[:5]

        # 3. sector tracking
        save_sector_history(top_sectors)

        img = build_heatmap()
        if img:
            send_image(img)

        emerging = detect_emerging_sectors()

        # 4. risk (KHÔNG dùng VNINDEX nữa)
        df_index = load_index()
        risk = market_risk(df_index)

        if risk >= 3:
            send("🚨 MARKET RISK HIGH - STOP")
            return

        # 5. market overview
        msg = "📊 MARKET\n\n"

        msg += "🔥 SECTORS:\n"
        for s, sc in top_sectors:
            msg += f"{s}: {round(sc,3)}\n"

        msg += "\n💪 STOCKS:\n"
        for s in top_stocks[:10]:
            msg += f"{s['symbol']} {round(s['score'],3)}\n"

        if emerging:
            msg += "\n🚀 Emerging:\n"
            for s, sc in emerging[:3]:
                msg += f"{s}: {round(sc,3)}\n"

        send(msg)

        # 6. entry scan
        for item in top_stocks:

            symbol = item["symbol"]

            try:
                df = load_stock_data(symbol)

                if detect_fake_breakout(df):
                    continue

                ok, fibo = validate_entry(df)

                if ok:
                    send(f"""
📈 {symbol}

Entry: {round(fibo["entry"],2)}
SL: {round(fibo["sl"],2)}
TP1: {round(fibo["tp1"],2)}
TP2: {round(fibo["tp2"],2)}
""")

            except Exception as e:
                log_error(f"{symbol}: {str(e)}")
                continue

    except Exception as e:
        log_error(f"MAIN ERROR: {str(e)}")
        send(f"❌ SYSTEM ERROR: {str(e)}")

    log_info("=== END RUN ===")


if __name__ == "__main__":
    main()
