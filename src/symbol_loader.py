import pandas as pd

def load_symbols():

    df = pd.read_csv("data/full_symbols.csv")

    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()

    # ❌ loại index / ETF / CW / rác
    df = df[~df["symbol"].str.contains("VNINDEX|VN30|HNX|UPCOM", na=False)]
    df = df[~df["symbol"].str.startswith(("E1", "FU", "CW", "C"), na=False)]

    # chỉ giữ cổ phiếu thường
    df = df[df["symbol"].str.len().between(2, 4)]

    df = df.dropna()

    return df.reset_index(drop=True)
