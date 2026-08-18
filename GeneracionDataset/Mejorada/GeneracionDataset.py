import csv
import random
from pathlib import Path

import networkx as nx
import numpy as np

# generar_red: (enlaces, conexiones, semilla)
def generar_red(n=100, m=4, seed=42):
    """
    Genera una red sintética utilizando el modelo Barabási-Albert
    y asigna métricas de Calidad de Servicio (QoS) a cada enlace.
    """
    #validacion de parámetros en el modelo Barabási-Albert
    if not 1 <= m < n:
        raise ValueError("Debe cumplirse 1 <= m < n")

    # genera el aleatorio con semilla fija para obtener resultados reproducibles
    rng = random.Random(seed)

    # Generador para calcular la utilización de los enlaces.
    np_rng = np.random.default_rng(seed)

    #se genera una red mediante el modelo Barabási-Albert
    #los nodos que tienen más conexiones tienen mayor probabilidad de recibir nuevas conexiones
    base = nx.barabasi_albert_graph( n=n, m=m, seed=seed)

    # Se convierte a grafo dirigido para permitir que cada enlace tenga metricas QoS independientes
    G = base.to_directed()

    # generacion de métricas de calidad de servicio (QoS) para cada enlace
    for u, v in G.edges():        
        # se genera una capacidad fisica del enlace entre 50 y 1000 Mbps
        capacidad = rng.uniform(50.0, 1000.0)

        # representa qué porcentaje de capacidad del enlace se encuentra actualmente ocupado
        utilizacion = float( np_rng.beta(2.0, 4.0))

        # - ANCHO DE BANDA DISPONIBLE -
        # Se calcula el ancho de banda disponible, se establece un mínimo de 1 Mbps para evitar valores muy pequeños
        ancho_disponible = max(1.0,capacidad * (1.0 - utilizacion))

        # retardo base del enlace - Se genera entre 1 y 45 milisegundos
        propagacion = rng.uniform( 1.0, 45.0)

        # - RETARDO POR COLA -
        #el retardo por cola aumenta conforme crece la utilización del enlace
        cola = ( 2.5 * utilizacion / max( 1.0 - utilizacion,0.05))

        # - LATENCIA -
        # Combina el retardo base, la congestión y una pequeña variación aleatoria
        latencia = (propagacion + cola + rng.uniform(0.0, 2.0))

        # - JITTER -
        # Aumenta con la congestion del enlace, pero no es idéntico a la latencia
        jitter = (rng.uniform(0.1, 3.0)+ rng.uniform(0.05, 0.25) * cola)

        # - PÉRDIDA DE PAQUETES -
        # Se genera una pérdida base entre 0.001 % y 0.2 %
        perdida_base = rng.uniform(0.00001, 0.002)

        # La pérdida aumenta cuando el enlace está más congestionado.
        perdida = (perdida_base + 0.03 * (utilizacion ** 4))

        # La pérdida de paquetes se limita a un máximo de 5 %
        perdida = min(max(perdida, 0.0), 0.05)

        # Cada enlace u -> v almacena sus propios valores de Calidad de Servicio
        G[u][v]["AnchoBanda"] = ancho_disponible
        G[u][v]["Latencia"] = latencia
        G[u][v]["jitter"] = jitter
        G[u][v]["PaquetesPerdidos"] = perdida

    # Retorna la red completa
    return G


def exportar_red_csv(G, filename):
    """
    Ayuda a exportar los enlaces y métricas QoS de la red a un archivo CSV.
    Cada fila representa un enlace dirigido: Origen -> Destino
    """

    #se convierte la ruta recibida en un Path
    filename = Path(filename)

    # se crean las carpetas necesarias en caso de que no existan
    filename.parent.mkdir(
        parents=True, exist_ok=True
    )

    # se abre el documento para escribir la informacion de la red
    with filename.open("w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)
        # encabezados que se le colocan al dataset
        writer.writerow([
            "Origen","Destino","AnchoBanda","Latencia","jitter","PaquetesPerdidos"
        ])

        # Se recorren todas las aristas de la red, para obtener los atributos de cada enlace
        for u, v, datos in G.edges(data=True):
            writer.writerow([
                u, v, datos["AnchoBanda"], datos["Latencia"], datos["jitter"], datos["PaquetesPerdidos"]
            ])


if __name__ == "__main__":
    # Se genera una red con: 100 nodos , m = 4 conexiones por nuevo nodo y la semilla = 42
    # (La semilla garantiza que la red generada sea reproducible entre ejecuciones)
    G = generar_red(n=100,m=4,seed=42)

    # Exportar la red generada a CSV
    exportar_red_csv(G, "../../Red_datasets/Mejorada/DatasetRed.csv")

    print("Dataset generado correctamente.")
    print(f"Número de nodos: {G.number_of_nodes()}")
    print(f"Número de enlaces dirigidos: {G.number_of_edges()}")