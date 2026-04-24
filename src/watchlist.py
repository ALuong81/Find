from data_loader import load_stock_data
from accumulation import detect_accumulation
from flow_timeline import flow_timeline


def build_watchlist(df_symbols):

    watchlist = []

    for _, row in df_symbols.iterrows():

        symbol = row["symbol"]

        try:
            df = load_stock_data(symbol)

            acc = detect_accumulation(df)
            flow = flow_timeline(df)

            if acc and flow > 0.3:
                watchlist.append(symbol)

        except:
            continue

    return watchlist
