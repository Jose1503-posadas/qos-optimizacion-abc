import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# leer desde el csv normalizado
df = pd.read_csv("DatasetRed_Normalizado.csv")

# crear grafo desde el archivo
G = nx.from_pandas_edgelist(
    df,
    source="Origen",
    target="Destino",
    create_using=nx.DiGraph()
)

# dibujar
plt.figure(figsize=(14,10))

pos = nx.spring_layout(
    G,
    seed=42
)

nx.draw(
    G,
    pos,
    with_labels=True,
    node_size=500,
    arrows=True
)

plt.title("Red generada desde CSV normalizado")
plt.axis("off")
plt.show()