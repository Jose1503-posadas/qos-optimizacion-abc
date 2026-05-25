from pathlib import Path
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent

csv_path = BASE_DIR.parent / "Red_datasets" / "DatasetRed_Normalizado.csv"

df = pd.read_csv(csv_path)

G = nx.from_pandas_edgelist( df, source="Origen", target="Destino", create_using=nx.DiGraph())

plt.figure(figsize=(14, 10))

pos = nx.spring_layout(G, seed=42)

nx.draw(G, pos, with_labels=True, node_size=500, arrows=True)

plt.title("Red generada desde CSV")
plt.axis("off")
plt.show()