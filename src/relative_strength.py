def relative_strength(df, df_index):

    r1 = df["close"].pct_change(20).iloc[-1]
    r2 = df_index["close"].pct_change(20).iloc[-1]

    return r1 - r2
