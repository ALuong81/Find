def position_size(capital, entry, sl):

    risk_per_trade = 0.02  # 2% vốn

    risk_amount = capital * risk_per_trade
    risk_per_share = abs(entry - sl)

    if risk_per_share == 0:
        return 0

    size = risk_amount / risk_per_share

    return int(size)
