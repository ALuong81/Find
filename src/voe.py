from relative_strength import relative_strength

def voe_score(df, df_index):

    close = df["close"]
    vol = df["volume"]

    rs = relative_strength(df, df_index)
    momentum = close.pct_change(10).iloc[-1]
    vol_ma = vol.rolling(20).mean()
    vol_score = vol.iloc[-1] / vol_ma.iloc[-1]

    return rs * 0.5 + momentum * 0.3 + vol_score * 0.2
