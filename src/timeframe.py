def resample_h1(df):

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    h1 = df.resample("1H").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    }).dropna()

    return h1.reset_index()
