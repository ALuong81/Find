import csv

def log_trade(symbol, entry, sl, tp1):

    with open("data/trades.csv", "a") as f:
        writer = csv.writer(f)
        writer.writerow([symbol, entry, sl, tp1])
