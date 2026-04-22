from logger import log_info

def execute(symbol, entry, sl, tp1, tp2):

    log_info(
        f"{symbol} | ENTRY={entry} | SL={sl} | TP1={tp1} | TP2={tp2}"
    )
