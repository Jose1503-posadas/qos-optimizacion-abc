from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent.parent
CSV_PATH = BASE_DIR / "Red_datasets" / "Mejorada" / "DatasetRed.csv"
OUTPUT_DIR = BASE_DIR / "VisualizacionDataset" / "Mejorada"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def cargar_red(csv_path):
    """Carga el dataset como un grafo dirigido."""

    df = pd.read_csv(csv_path)

    return nx.from_pandas_edgelist(
        df,
        source="Origen",
        target="Destino",
        edge_attr=["AnchoBanda","Latencia","jitter","PaquetesPerdidos",],
        create_using=nx.DiGraph(),
    )

def visualizar_red(G, filename="Red_dataset.png"):
    """Visualiza la topología y destaca los nodos más conectados."""

    # Para analizar conectividad sin considerar dirección
    G_undirected = G.to_undirected()

    grados = dict(G_undirected.degree())
    valores = np.array(list(grados.values()))

    grado_promedio = valores.mean()
    grado_maximo = valores.max()

    # Nodos con mayor conectividad
    hubs = sorted(grados.items(),key=lambda x: x[1], reverse=True,)[:10]

    # Posición de los nodos
    pos = nx.spring_layout(G_undirected,seed=42,k=2.0 / np.sqrt(G.number_of_nodes()),iterations=500,)

    # Tamaño y color según conectividad
    node_sizes = [100 + np.sqrt(grados[nodo]) * 110 for nodo in G.nodes()]
    node_colors = [grados[nodo]for nodo in G.nodes()]

    # Figura
    fig, ax = plt.subplots(figsize=(18, 14), facecolor="white",)

    # Enlaces
    nx.draw_networkx_edges(G,pos,ax=ax,arrows=True,arrowstyle="-|>",arrowsize=7,width=0.65,alpha=0.14,connectionstyle="arc3,rad=0.035", node_size=node_sizes,)

    # Nodos
    nodos = nx.draw_networkx_nodes(G,pos,ax=ax,node_size=node_sizes,node_color=node_colors,cmap=plt.cm.viridis,alpha=0.92,linewidths=0.7,edgecolors="white",)
    etiquetas = {nodo: str(nodo) for nodo, _ in hubs }
    nx.draw_networkx_labels(G,pos,labels=etiquetas,ax=ax,font_size=10,font_weight="bold",bbox={"facecolor": "white","edgecolor": "none","alpha": 0.8,"pad": 1.5,},)
    cbar = fig.colorbar(nodos,ax=ax,shrink=0.7,pad=0.01,)

    cbar.set_label("Número de conexiones del nodo", fontsize=11,)

    informacion = (
        f"Nodos: {G.number_of_nodes()}\n"
        f"Enlaces dirigidos: {G.number_of_edges()}\n"
        f"Grado promedio: {grado_promedio:.2f}\n"
        f"Grado máximo: {grado_maximo}"
    )

    ax.text(0.015,0.015,informacion,transform=ax.transAxes,fontsize=10,verticalalignment="bottom",bbox={"boxstyle": "round,pad=0.6","facecolor": "white","edgecolor": "lightgray","alpha": 0.9,},)

    ax.set_title(("Topología de la red QoS"),fontsize=18,fontweight="bold",pad=20,)

    ax.axis("off")
    plt.tight_layout()

    output = OUTPUT_DIR /filename
    plt.savefig(output,dpi=300,bbox_inches="tight", facecolor="white",)
    plt.show()

if __name__ == "__main__":
    G = cargar_red(CSV_PATH)
    visualizar_red(G)