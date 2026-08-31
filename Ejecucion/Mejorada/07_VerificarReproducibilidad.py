from pathlib import Path
import sys

import networkx as nx
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from Algoritmo.Mejorada.AlgoritmoABC import ABCMultiobjetivo

DATASET = BASE_DIR/"Red_datasets"/"Mejorada"/"DatasetRed.csv"
OUTPUT_DIR = BASE_DIR/"Resultados"/"Mejorada"/"04_Reproducibilidad"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ORIGEN, DESTINO = 52, 96
NUM_ABEJAS = 30
MAX_ITERACIONES = 250
MAX_PARETO = 100
MAX_LONGITUD_RUTA = 25
LIMITE = 60
SEED = 42


def cargar_grafo(archivo):
    df = pd.read_csv(archivo)
    G = nx.DiGraph()

    for _, f in df.iterrows():
        G.add_edge(
            int(f["Origen"]), int(f["Destino"]),
            AnchoBanda=float(f["AnchoBanda"]),
            Latencia=float(f["Latencia"]),
            jitter=float(f["jitter"]),
            PaquetesPerdidos=float(f["PaquetesPerdidos"])
        )

    return G


def ejecutar(G):
    abc = ABCMultiobjetivo(
        G, ORIGEN, DESTINO,
        num_abejas=NUM_ABEJAS,
        max_iteraciones=MAX_ITERACIONES,
        max_pareto=MAX_PARETO,
        max_longitud_ruta=MAX_LONGITUD_RUTA,
        limite=LIMITE,
        seed=SEED
    )

    frente = abc.ejecutar()

    pareto = pd.DataFrame([
        {
            "Ruta": "->".join(map(str, ruta)),
            "Latencia": fitness[0],
            "Perdida": fitness[1],
            "Jitter": fitness[2],
            "AnchoBanda": -fitness[3]
        }
        for ruta, fitness in frente
    ])

    historial = pd.DataFrame(abc.historial)
    poblacion = [tuple(r) for r in abc.poblacion]

    return pareto, historial, poblacion


def ordenar_pareto(df):
    return df.sort_values(
        ["Ruta", "Latencia", "Perdida", "Jitter", "AnchoBanda"]
    ).reset_index(drop=True)


def main():
    if not DATASET.exists():
        raise FileNotFoundError(f"No se encontró:\n{DATASET}")

    G = cargar_grafo(DATASET)

    print("=" * 65)
    print("PRUEBA DE REPRODUCIBILIDAD")
    print("=" * 65)
    print(f"Seed: {SEED} | Abejas: {NUM_ABEJAS} | Iteraciones: {MAX_ITERACIONES}\n")

    print("Ejecutando corrida A...")
    pareto_a, historial_a, poblacion_a = ejecutar(G)

    print("Ejecutando corrida B...")
    pareto_b, historial_b, poblacion_b = ejecutar(G)

    mismo_pareto = ordenar_pareto(pareto_a).equals(ordenar_pareto(pareto_b))
    mismo_historial = historial_a.equals(historial_b)
    misma_poblacion = poblacion_a == poblacion_b

    resultado = pd.DataFrame([{
        "Seed": SEED,
        "MismoFrentePareto": mismo_pareto,
        "MismoHistorial": mismo_historial,
        "MismaPoblacionFinal": misma_poblacion,
        "Reproducible": mismo_pareto and mismo_historial and misma_poblacion
    }])

    pareto_a.to_csv(OUTPUT_DIR / "FrentePareto_A.csv", index=False)
    pareto_b.to_csv(OUTPUT_DIR / "FrentePareto_B.csv", index=False)
    historial_a.to_csv(OUTPUT_DIR / "Historial_A.csv", index=False)
    historial_b.to_csv(OUTPUT_DIR / "Historial_B.csv", index=False)
    resultado.to_csv(OUTPUT_DIR / "VerificacionReproducibilidad.csv", index=False)


    print(f"Frente Pareto idéntico:   {'SI' if mismo_pareto else 'NO'}")
    print(f"Historial idéntico:       {'SI' if mismo_historial else 'NO'}")
    print(f"Población final idéntica: {'SI' if misma_poblacion else 'NO'}")

if __name__ == "__main__":
    main()