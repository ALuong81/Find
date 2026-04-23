def backtest(df):

    wins = 0
    losses = 0

    for i in range(60, len(df)-5):

        sub = df.iloc[:i]

        ok, f = validate_entry(sub)

        if not ok:
            continue

        future = df.iloc[i:i+5]

        hit_tp = future["high"].max() >= f["tp1"]
        hit_sl = future["low"].min() <= f["sl"]

        if hit_tp:
            wins += 1
        elif hit_sl:
            losses += 1

    total = wins + losses

    if total == 0:
        return 0

    return wins / total
