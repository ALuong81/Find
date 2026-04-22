from symbol_loader import load_symbols
from market_ranking import market_ranking
from sector_ranking import sector_ranking
from data_loader import load_stock_data
from fake_breakout import detect_fake_breakout
from entry import validate_entry
from risk import market_risk
from alert import send

df_symbols = load_symbols()

market = market_ranking(df_symbols, load_stock_data)

top_stocks = market[:20]
top_sectors = sector_ranking(market)[:5]

df_index = load_stock_data("VNINDEX")

if market_risk(df_index) >= 3:
    send("🚨 MARKET RISK HIGH")
    exit()

msg = "📊 MARKET\n\n"

msg += "🔥 SECTORS:\n"
for s, sc in top_sectors:
    msg += f"{s}: {round(sc,3)}\n"

msg += "\n💪 TOP STOCKS:\n"
for s in top_stocks[:10]:
    msg += f"{s['symbol']} {round(s['score'],3)}\n"

send(msg)

for s in top_stocks:

    df = load_stock_data(s["symbol"])

    if detect_fake_breakout(df):
        continue

    ok, f = validate_entry(df)

    if ok:
        send(f"""
📈 {s["symbol"]}

Entry: {round(f["entry"],2)}
SL: {round(f["sl"],2)}
TP1: {round(f["tp1"],2)}
TP2: {round(f["tp2"],2)}
""")
