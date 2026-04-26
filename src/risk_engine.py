def position_size(equity, risk_per_trade, entry, sl):

    risk = equity * risk_per_trade

    if entry == sl:
        return 0

    size = risk / abs(entry - sl)

    return size


def adjust_by_regime(size, regime):

    if regime == "SAFE":
        return size * 0.5
    elif regime == "OFF":
        return 0
    else:
        return size
