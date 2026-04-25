def get_market_mode(market_score):

    if market_score <= 0:
        return "OFF"

    if market_score == 1:
        return "SAFE"

    return "AGGRESSIVE"
