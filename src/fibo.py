def fibo(df):

    # lấy 50 nến gần nhất
    recent = df.tail(50)

    high = recent["high"].max()
    low = recent["low"].min()

    diff = high - low

    # 🔥 fibonacci levels
    entry = high - diff * 0.5      # pullback 50%
    sl = low                       # stop loss đáy
    tp1 = high                     # target 1
    tp2 = high + diff * 0.5        # target 2 mở rộng

    return {
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2
    }
