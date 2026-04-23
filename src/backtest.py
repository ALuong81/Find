from entry import validate_entry

def backtest(df):

    wins, losses = 0, 0

    for i in range(60, len(df)-5):

        sub = df.iloc[:i]

        ok, f = validate_entry(sub)
        if not ok:
            continue

        future = df.iloc[i:i+5]

        if future["high"].max() >= f["tp1"]:
            wins += 1
        elif future["low"].min() <= f["sl"]:
            losses += 1

    total = wins + losses
    return wins/total if total else 0
