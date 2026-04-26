def mtf_score(df_d, df_h1):

    if df_h1 is None or len(df_h1) < 20:
        return 0

    try:
        h1_close = df_h1["close"]

        ma20 = h1_close.rolling(20).mean().iloc[-1]
        price = h1_close.iloc[-1]

        if price > ma20:
            return 1
        else:
            return -1

    except:
        return 0
