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
OPTIMOS = BASE_DIR/"Resultados"/"Mejorada"/"01_Verificacion"/"OptimosExactos.csv"
OUTPUT_DIR= BASE_DIR/"Resultados"/"Mejorada"/"02_ExperimentoIteraciones"
CORRIDAS_DIR = OUTPUT_DIR/"Corridas"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CORRIDAS_DIR.mkdir(parents=True, exist_ok=True)

ARCHIVO_CORRIDAS = OUTPUT_DIR/"ResultadosPorCorrida.csv"
ARCHIVO_RESUMEN = OUTPUT_DIR/"ResumenPorIteraciones.csv"

ORIGEN, DESTINO = 52, 96
NUM_ABEJAS = 30
MAX_PARETO = 100
MAX_LONGITUD_RUTA = 25
LIMITE = 60

ITERACIONES = [25, 50, 100, 150, 250, 400]
SEEDS = range(1, 11)

TOLERANCIA = 1e-9

def cargar_grafo(archivo):
    """Carga la red QoS desde el dataset."""

    df = pd.read_csv(archivo)
    G = nx.DiGraph()

    for _, f in df.iterrows():
        G.add_edge(int(f["Origen"]), int(f["Destino"]),AnchoBanda=float(f["AnchoBanda"]),Latencia=float(f["Latencia"]),jitter=float(f["jitter"]),PaquetesPerdidos=float(f["PaquetesPerdidos"]))

    return G


def cargar_optimos(archivo):
    """Carga los óptimos exactos obtenidos en el Paso 1C."""

    df = pd.read_csv(archivo)
    return dict(zip(df["Metrica"], df["Optimo"]))


def gap_minimo(valor, optimo):
    """Gap porcentual para objetivos que se minimizan."""
    return max(0.0, (valor-optimo)/optimo*100)


def gap_maximo(valor, optimo):
    """Gap porcentual para objetivos que se maximizan."""
    return max(0.0, (optimo-valor)/optimo*100)


def guardar_pareto(frente, iteraciones, seed):
    """Guarda el frente Pareto de cada ejecución."""

    filas = []

    for i, (ruta, fitness) in enumerate(frente, start=1):
        filas.append({"Solucion": i,"Ruta": "->".join(map(str, ruta)),"Saltos": len(ruta) - 1,"Latencia": fitness[0],"Perdida": fitness[1],"Jitter": fitness[2],"AnchoBanda": -fitness[3]})

    archivo = CORRIDAS_DIR / f"Pareto_iter{iteraciones}_seed{seed:02d}.csv"
    pd.DataFrame(filas).to_csv(archivo, index=False)


def ejecutar_corrida(G, optimos, iteraciones, seed):
    """Ejecuta una configuración y obtiene sus indicadores finales."""

    inicio = time.perf_counter()

    abc = ABCMultiobjetivo(G, ORIGEN, DESTINO,num_abejas=NUM_ABEJAS,max_iteraciones=iteraciones,max_pareto=MAX_PARETO,max_longitud_ruta=MAX_LONGITUD_RUTA,limite=LIMITE,seed=seed)

    frente = abc.ejecutar()
    tiempo = time.perf_counter() - inicio
    fitness = np.array([f for _, f in frente], dtype=float)
    latencia = float(fitness[:, 0].min())
    perdida = float(fitness[:, 1].min())
    jitter = float(fitness[:, 2].min())
    ancho_banda = float((-fitness[:, 3]).max())
    gap_latencia = gap_minimo(latencia, optimos["Latencia"])
    gap_perdida = gap_minimo(perdida, optimos["Perdida"])
    gap_jitter = gap_minimo(jitter, optimos["Jitter"])
    gap_bw = gap_maximo(ancho_banda, optimos["AnchoBanda"])
    opt_lat = math.isclose(latencia, optimos["Latencia"], rel_tol=TOLERANCIA, abs_tol=TOLERANCIA)
    opt_per = math.isclose(perdida, optimos["Perdida"], rel_tol=TOLERANCIA, abs_tol=TOLERANCIA)
    opt_jit = math.isclose(jitter, optimos["Jitter"], rel_tol=TOLERANCIA, abs_tol=TOLERANCIA)
    opt_bw = math.isclose(ancho_banda, optimos["AnchoBanda"], rel_tol=TOLERANCIA, abs_tol=TOLERANCIA)

    historial_final = abc.historial[-1]

    guardar_pareto(frente, iteraciones, seed)

    return {
        "Iteraciones": iteraciones,
        "Seed": seed,
        "TiempoSegundos": tiempo,
        "TamanoPareto": len(frente),
        "PoblacionUnica": historial_final["PoblacionUnica"],
        "DiversidadRutas": historial_final["DiversidadRutas"],

        "MejorLatencia": latencia,
        "MejorPerdida": perdida,
        "MejorJitter": jitter,
        "MejorAnchoBanda": ancho_banda,

        "GapLatencia": gap_latencia,
        "GapPerdida": gap_perdida,
        "GapJitter": gap_jitter,
        "GapAnchoBanda": gap_bw,

        "OptimoLatencia": opt_lat,
        "OptimoPerdida": opt_per,
        "OptimoJitter": opt_jit,
        "OptimoAnchoBanda": opt_bw,

        "OptimosAlcanzados": sum([opt_lat, opt_per, opt_jit, opt_bw]),
        "TodosOptimos": opt_lat and opt_per and opt_jit and opt_bw
    }


def generar_resumen(df):
    """Resume las 10 semillas para cada cantidad de iteraciones."""

    filas = []

    for iteraciones, grupo in df.groupby("Iteraciones"):
        filas.append({
            "Iteraciones": iteraciones,
            "Corridas": len(grupo),

            "TiempoPromedio": grupo["TiempoSegundos"].mean(),
            "TiempoMediano": grupo["TiempoSegundos"].median(),

            "ParetoPromedio": grupo["TamanoPareto"].mean(),
            "ParetoMediano": grupo["TamanoPareto"].median(),
            "DiversidadPromedio": grupo["DiversidadRutas"].mean(),

            "GapLatenciaPromedio": grupo["GapLatencia"].mean(),
            "GapPerdidaPromedio": grupo["GapPerdida"].mean(),
            "GapJitterPromedio": grupo["GapJitter"].mean(),
            "GapAnchoBandaPromedio": grupo["GapAnchoBanda"].mean(),

            "ExitoLatencia": grupo["OptimoLatencia"].mean() * 100,
            "ExitoPerdida": grupo["OptimoPerdida"].mean() * 100,
            "ExitoJitter": grupo["OptimoJitter"].mean() * 100,
            "ExitoAnchoBanda": grupo["OptimoAnchoBanda"].mean() * 100,
            "ExitoCompleto": grupo["TodosOptimos"].mean() * 100,

            "OptimosPromedio": grupo["OptimosAlcanzados"].mean()
        })

    return pd.DataFrame(filas)


def main():
    if not DATASET.exists():
        raise FileNotFoundError(f"No se encontró:\n{DATASET}")

    if not OPTIMOS.exists():
        raise FileNotFoundError(
            f"No se encontró:\n{OPTIMOS} - Ejecuta primero 03_VerificarOptimosExactos.py.")

    G = cargar_grafo(DATASET)
    optimos = cargar_optimos(OPTIMOS)
    resultados = []
    total = len(ITERACIONES) * len(SEEDS)
    corrida = 0

    for iteraciones in ITERACIONES:
        print(f"\n{iteraciones} ITERACIONES")

        for seed in SEEDS:
            corrida += 1
            print(f"[{corrida:02d}/{total}] Seed {seed} -", end=" ", flush=True)

            resultado = ejecutar_corrida(G, optimos, iteraciones, seed)
            resultados.append(resultado)

            print(f"Pareto={resultado['TamanoPareto']} | " f"Óptimos={resultado['OptimosAlcanzados']}/4 | " f"{resultado['TiempoSegundos']:.1f}s")

            # Guarda avances por si la ejecución se interrumpe
            pd.DataFrame(resultados).to_csv(ARCHIVO_CORRIDAS, index=False)

    df = pd.DataFrame(resultados)
    resumen = generar_resumen(df)

    df.to_csv(ARCHIVO_CORRIDAS, index=False)
    resumen.to_csv(ARCHIVO_RESUMEN, index=False)

    columnas = ["Iteraciones","TiempoPromedio","ParetoPromedio","DiversidadPromedio","ExitoLatencia","ExitoPerdida","ExitoJitter","ExitoAnchoBanda","ExitoCompleto"]
    print(resumen[columnas].round(4).to_string(index=False))

if __name__ == "__main__":
    main()