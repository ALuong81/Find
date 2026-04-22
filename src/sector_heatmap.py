import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def build_heatmap():

    try:
        df = pd.read_csv("data/sector_flow.csv")
    except:
        return None

    pivot = df.pivot(index="date", columns="sector", values="score")

    plt.figure(figsize=(10, 5))
    sns.heatmap(pivot, cmap="RdYlGn", center=0)

    os.makedirs("data", exist_ok=True)
    path = "data/heatmap.png"

    plt.savefig(path, bbox_inches="tight")
    plt.close()

    return path
