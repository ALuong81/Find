import pandas as pd
import os
from datetime import datetime

def save_sector_history(sectors):

    os.makedirs("data", exist_ok=True)

    rows = []
    today = datetime.now().strftime("%Y-%m-%d")

    for s, score in sectors:
        rows.append({
            "date": today,
            "sector": s,
            "score": score
        })

    df = pd.DataFrame(rows)

    df.to_csv(
        "data/sector_flow.csv",
        mode="a",
        header=not os.path.exists("data/sector_flow.csv"),
        index=False
    )
