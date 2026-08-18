from pathlib import Path
import pandas as pd
import networkx as nx

from QoS_ABC.ABC_Algoritmo import ABCMultiobjetivo


BASE_DIR = Path(__file__).resolve().parent

DATASET = BASE_DIR / "Red_datasets" / "DatasetRed_Normalizado.csv"
PARETO = BASE_DIR / "Red_datasets" / "FitnessResultados.csv"


def cargar_grafo(archivo_csv):

    df = pd.read_csv(archivo_csv)
    G = nx.DiGraph()

    for _, fila in df.iterrows():
        G.add_edge( int(fila["Origen"]), int(fila["Destino"]), AnchoBanda=float(fila["AnchoBanda"]), Latencia=float(fila["Latencia"]), jitter=float(fila["jitter"]), PaquetesPerdidos=float(fila["PaquetesPerdidos"]))
    return G


def ejecutar_abc( archivo_csv, origen, destino, num_abejas, max_iteraciones):

    G = cargar_grafo(archivo_csv)
    abc = ABCMultiobjetivo(G, origen, destino, num_abejas,  max_iteraciones)
    frente_pareto = abc.ejecutar()
    pd.DataFrame({  "Iteracion": range(1, len(abc.historial) + 1), "MejorFitness": abc.historial }).to_csv( PARETO, index=False)

    return frente_pareto


def mostrar_resultados(frente_pareto):

    print("\nFRENTE DE PARETOn")

    for i, (ruta, fitness) in enumerate(frente_pareto, start=1):
        print(f"Solución {i}")
        print("Ruta:")
        print(ruta)
        print("Fitness:")
        print(f"Latencia: {fitness[0]:.4f}")
        print(f"Pérdida: {fitness[1]:.4f}")
        print(f"Jitter: {fitness[2]:.4f}")
        print(f"Ancho de banda: {fitness[3]:.4f}")
        print("-" * 40)


def main():

    frente_pareto = ejecutar_abc( archivo_csv=DATASET, origen=0, destino=20, num_abejas=30, max_iteraciones=100)
    mostrar_resultados(frente_pareto)


if __name__ == "__main__":
    main()