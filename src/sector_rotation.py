import pandas as pd

def sector_rotation(sector_df):

    if len(sector_df) < 5:
        return sector_df

    df = sector_df.copy()

    # 🔥 EMA smoothing
    df["ema"] = df.groupby("sector")["score"].transform(
        lambda x: x.ewm(span=3).mean()
    )

    # 🔥 momentum ngành
    df["momentum"] = df.groupby("sector")["ema"].diff()

    # 🔥 score tổng hợp
    df["rotation_score"] = df["score"] * 0.7 + df["momentum"].fillna(0) * 0.3

    return df.sort_values("rotation_score", ascending=False)
