from pathlib import Path
import math
import sys
import time
import networkx as nx
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from Algoritmo.Mejorada.AlgoritmoABC import ABCMultiobjetivo

DATASET = BASE_DIR/"Red_datasets"/"Mejorada"/"DatasetRed.csv"
OPTIMOS = BASE_DIR /"Resultados"/"Mejorada"/"01_Verificacion"/"OptimosExactos.csv"
OUTPUT_DIR = BASE_DIR /"Resultados"/"Mejorada"/"03_MultiplesSemillas"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVO_CORRIDAS = OUTPUT_DIR/"ResumenCorridas.csv"
ARCHIVO_ESTADISTICAS = OUTPUT_DIR/"ResumenEstadistico.csv"
ORIGEN, DESTINO = 52, 96
NUM_ABEJAS = 30
MAX_ITERACIONES = 250
MAX_PARETO = 100
MAX_LONGITUD_RUTA = 25
LIMITE = 60
SEEDS = range(1, 31)
TOLERANCIA = 1e-9


def cargar_grafo(archivo):
    df = pd.read_csv(archivo)
    G = nx.DiGraph()

    for _, f in df.iterrows():
        G.add_edge(int(f["Origen"]), int(f["Destino"]),AnchoBanda=float(f["AnchoBanda"]),Latencia=float(f["Latencia"]),jitter=float(f["jitter"]),PaquetesPerdidos=float(f["PaquetesPerdidos"]))
    return G


def cargar_optimos(archivo):
    df = pd.read_csv(archivo)
    return dict(zip(df["Metrica"], df["Optimo"]))


def gap(valor, optimo, minimizar=True):
    if minimizar:
        return max(0.0, (valor - optimo) / optimo * 100)
    return max(0.0, (optimo - valor) / optimo * 100)


def guardar_resultados_seed(seed, abc, frente):
    carpeta = OUTPUT_DIR / f"Seed_{seed:02d}"
    carpeta.mkdir(parents=True, exist_ok=True)

    filas = []

    for i, (ruta, fitness) in enumerate(frente, start=1):
        filas.append({"Solucion": i,"Ruta": "->".join(map(str, ruta)),"Saltos": len(ruta) - 1,"Latencia": fitness[0],"Perdida": fitness[1],"Jitter": fitness[2],"AnchoBanda": -fitness[3]})

    pd.DataFrame(filas).to_csv(carpeta / "FrentePareto.csv", index=False)
    pd.DataFrame(abc.historial).to_csv(carpeta / "HistorialABC.csv", index=False)


def ejecutar_seed(G, optimos, seed):
    inicio = time.perf_counter()

    abc = ABCMultiobjetivo(
        G, ORIGEN, DESTINO,
        num_abejas=NUM_ABEJAS,
        max_iteraciones=MAX_ITERACIONES,
        max_pareto=MAX_PARETO,
        max_longitud_ruta=MAX_LONGITUD_RUTA,
        limite=LIMITE,
        seed=seed
    )

    frente = abc.ejecutar()
    tiempo = time.perf_counter() - inicio
    fitness = np.array([f for _, f in frente], dtype=float)

    lat = float(fitness[:, 0].min())
    perdida = float(fitness[:, 1].min())
    jitter = float(fitness[:, 2].min())
    bw = float((-fitness[:, 3]).max())

    opt_lat = math.isclose(lat, optimos["Latencia"], rel_tol=TOLERANCIA, abs_tol=TOLERANCIA)
    opt_per = math.isclose(perdida, optimos["Perdida"], rel_tol=TOLERANCIA, abs_tol=TOLERANCIA)
    opt_jit = math.isclose(jitter, optimos["Jitter"], rel_tol=TOLERANCIA, abs_tol=TOLERANCIA)
    opt_bw = math.isclose(bw, optimos["AnchoBanda"], rel_tol=TOLERANCIA, abs_tol=TOLERANCIA)

    guardar_resultados_seed(seed, abc, frente)
    final = abc.historial[-1]

    return {
        "Seed": seed,
        "TiempoSegundos": tiempo,
        "TamanoPareto": len(frente),
        "PoblacionUnica": final["PoblacionUnica"],
        "DiversidadRutas": final["DiversidadRutas"],
        "MejorLatencia": lat,
        "MejorPerdida": perdida,
        "MejorJitter": jitter,
        "MejorAnchoBanda": bw,
        "GapLatencia": gap(lat, optimos["Latencia"]),
        "GapPerdida": gap(perdida, optimos["Perdida"]),
        "GapJitter": gap(jitter, optimos["Jitter"]),
        "GapAnchoBanda": gap(bw, optimos["AnchoBanda"], minimizar=False),
        "OptimoLatencia": opt_lat,
        "OptimoPerdida": opt_per,
        "OptimoJitter": opt_jit,
        "OptimoAnchoBanda": opt_bw,
        "OptimosAlcanzados": sum([opt_lat, opt_per, opt_jit, opt_bw]),
        "TodosOptimos": opt_lat and opt_per and opt_jit and opt_bw
    }


def generar_estadisticas(df):
    metricas = [
        "TiempoSegundos", "TamanoPareto", "DiversidadRutas",
        "MejorLatencia", "MejorPerdida", "MejorJitter", "MejorAnchoBanda",
        "GapLatencia", "GapPerdida", "GapJitter", "GapAnchoBanda"
    ]

    filas = []

    for metrica in metricas:
        s = df[metrica]
        filas.append({"Metrica": metrica,"Media": s.mean(),"Mediana": s.median(),"DesviacionEstandar": s.std(),"Minimo": s.min(),"Maximo": s.max()})

    return pd.DataFrame(filas)


def mostrar_resumen(df):
    print("\n" + "=" * 70)
    print("RESUMEN - 30 SEMILLAS")
    print("=" * 70)
    print(f"Corridas:                    {len(df)}")
    print(f"Tiempo promedio:             {df['TiempoSegundos'].mean():.2f} s")
    print(f"Pareto promedio:             {df['TamanoPareto'].mean():.2f}")
    print(f"Diversidad promedio:         {df['DiversidadRutas'].mean():.4f}")
    print(f"Éxito latencia:              {df['OptimoLatencia'].mean() * 100:.2f} %")
    print(f"Éxito pérdida:               {df['OptimoPerdida'].mean() * 100:.2f} %")
    print(f"Éxito jitter:                {df['OptimoJitter'].mean() * 100:.2f} %")
    print(f"Éxito ancho de banda:        {df['OptimoAnchoBanda'].mean() * 100:.2f} %")
    print(f"Éxito completo:              {df['TodosOptimos'].mean() * 100:.2f} %")


def main():
    if not DATASET.exists():
        raise FileNotFoundError(f"No se encontró:\n{DATASET}")

    if not OPTIMOS.exists():
        raise FileNotFoundError(
            f"No se encontró:\n{OPTIMOS}\n"
            "Ejecuta primero 03_VerificarOptimosExactos.py."
        )

    G = cargar_grafo(DATASET)
    optimos = cargar_optimos(OPTIMOS)
    resultados = []

    for i, seed in enumerate(SEEDS, start=1):
        print(f"[{i:02d}/30] Seed {seed}...", end=" ", flush=True)

        resultado = ejecutar_seed(G, optimos, seed)
        resultados.append(resultado)

        print(
            f"Pareto={resultado['TamanoPareto']} | "
            f"Óptimos={resultado['OptimosAlcanzados']}/4 | "
            f"{resultado['TiempoSegundos']:.1f}s"
        )

        pd.DataFrame(resultados).to_csv(ARCHIVO_CORRIDAS, index=False)

    df = pd.DataFrame(resultados)
    estadisticas = generar_estadisticas(df)

    df.to_csv(ARCHIVO_CORRIDAS, index=False)
    estadisticas.to_csv(ARCHIVO_ESTADISTICAS, index=False)

    mostrar_resumen(df)

if __name__ == "__main__":
    main()