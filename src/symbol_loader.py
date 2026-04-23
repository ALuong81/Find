import pandas as pd

def load_symbols():

    df = pd.read_csv("data/full_symbols.csv")

    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()

    # lọc sạch
    df = df[df["symbol"].str.len().between(2, 4)]
    df = df[~df["symbol"].str.startswith(("E1", "FU", "CW", "C"))]

    # 🔥 chỉ giữ 80 mã tránh rate limit
    return df.head(80).reset_index(drop=True)
