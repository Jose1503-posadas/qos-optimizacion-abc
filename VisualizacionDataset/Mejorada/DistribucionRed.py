from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd


# Rutas
BASE_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = BASE_DIR / "Red_datasets" / "Mejorada" / "DatasetRed.csv"
OUTPUT_DIR = BASE_DIR / "VisualizacionDataset" / "Mejorada"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def cargar_red(csv_path):
    """Carga la red dirigida conservando las métricas QoS."""

    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró el dataset:\n{csv_path}")

    df = pd.read_csv(csv_path)

    columnas = ["Origen","Destino","AnchoBanda","Latencia","jitter","PaquetesPerdidos",]
    faltantes = [col for col in columnas if col not in df.columns]

    if faltantes:
        raise ValueError(f"Faltan columnas en el dataset: {', '.join(faltantes)}")

    return nx.from_pandas_edgelist(df,source="Origen",target="Destino",edge_attr=columnas[2:],create_using=nx.DiGraph(),)


def analizar_conectividad(G):
    """Calcula la conectividad de los nodos."""

    grados = dict(G.to_undirected().degree())
    valores = np.array(list(grados.values()))

    estadisticas = {
        "nodos": G.number_of_nodes(),
        "enlaces": G.number_of_edges(),
        "grado_minimo": int(valores.min()),
        "grado_promedio": float(valores.mean()),
        "grado_mediano": float(np.median(valores)),
        "grado_maximo": int(valores.max()),
    }

    hubs = sorted(grados.items(), key=lambda x: x[1], reverse=True)

    return valores, estadisticas, hubs


def visualizar_distribucion(grados, estadisticas):
    """Genera la gráfica de distribución de conectividad."""

    # distribución de conectividad
    valores, frecuencias = np.unique(grados, return_counts=True)
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.bar(valores, frecuencias, width=0.8, alpha=0.85, label="Cantidad de nodos",)

    promedio = estadisticas["grado_promedio"]
    maximo = estadisticas["grado_maximo"]

    ax.axvline(promedio,linestyle="--", linewidth=1.5, label=f"Grado promedio = {promedio:.2f}",)

    # Señalar nodo con mayor conectividad
    if maximo in valores:
        frecuencia = frecuencias[np.where(valores == maximo)[0][0]]

        ax.annotate(f"Mayor conectividad\n{maximo} conexiones",xy=(maximo, frecuencia),xytext=(maximo * 0.72, frecuencia + 3),arrowprops={"arrowstyle": "->"},fontsize=10,
)

    informacion = (f"Nodos: {estadisticas['nodos']}\n" f"Grado promedio: {promedio:.2f}\n" f"Grado máximo: {maximo}")

    ax.text(0.98, 0.95, informacion, transform=ax.transAxes, ha="right", va="top", fontsize=10, bbox={"boxstyle": "round,pad=0.5", "alpha": 0.8},)

    ax.set_title("Distribución de conectividad de la red",fontsize=17,fontweight="bold",pad=15,)

    ax.set_xlabel("Número de conexiones del nodo (grado)", fontsize=12)
    ax.set_ylabel("Cantidad de nodos", fontsize=12)

    ax.grid(axis="y", alpha=0.2)
    ax.legend()
    ax.yaxis.get_major_locator().set_params(integer=True)

    plt.tight_layout()

    output = OUTPUT_DIR / "DistribucionConectividad.png"
    plt.savefig(output, dpi=300, bbox_inches="tight")

    plt.show()


def main():

    G = cargar_red(CSV_PATH)
    grados, estadisticas, hubs = analizar_conectividad(G)
    visualizar_distribucion(grados, estadisticas)


if __name__ == "__main__":
    main()