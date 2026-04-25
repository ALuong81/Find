def optimize_threshold(results):

    best = None
    best_score = -999

    for r in [1.2, 1.5, 2.0]:
        win = results[results["rr"] > r]

        if len(win) == 0:
            continue

        score = win["equity"].iloc[-1]

        if score > best_score:
            best_score = score
            best = r

    return best
