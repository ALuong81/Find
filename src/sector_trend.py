import pandas as pd

def detect_emerging_sectors():

    try:
        df = pd.read_csv("data/sector_flow.csv")
    except:
        return []

    sectors = df["sector"].unique()
    res = []

    for s in sectors:

        sub = df[df["sector"] == s].sort_values("date")

        if len(sub) < 5:
            continue

        recent = sub["score"].tail(3).mean()
        past = sub["score"].head(len(sub)-3).mean()

        if recent > past * 1.5 and recent > 0:
            res.append((s, recent))

    return sorted(res, key=lambda x: x[1], reverse=True)
