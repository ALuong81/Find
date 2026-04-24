def relative_strength(df_stock, df_index):

    try:
        if df_stock is None or df_index is None:
            return 0

        if len(df_stock) < 30 or len(df_index) < 30:
            return 0

        stock_return = df_stock["close"].pct_change(20).iloc[-1]
        index_return = df_index["close"].pct_change(20).iloc[-1]

        rs = stock_return - index_return

        return rs

    except Exception as e:
        print("RS ERROR:", e)
        return 0
