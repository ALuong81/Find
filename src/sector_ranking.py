def sector_ranking(market):

    m = {}

    for i in market:
        m.setdefault(i["sector"], []).append(i["score"])

    res = []

    for s, scores in m.items():
        top = sorted(scores, reverse=True)[:5]
        res.append((s, sum(top)/len(top)))

    return sorted(res, key=lambda x: x[1], reverse=True)
