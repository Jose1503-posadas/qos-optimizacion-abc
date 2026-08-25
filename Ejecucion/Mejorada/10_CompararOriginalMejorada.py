from pathlib import Path
import math
import random
import sys
import time

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

# Cambia únicamente esta línea si tu archivo original tiene otro nombre.
from Algoritmo.Original.AlgoritmoABC import ABCMultiobjetivo as ABCOriginal
from Algoritmo.Mejorada.AlgoritmoABC import ABCMultiobjetivo as ABCMejorada


# ============================================================
# CONFIGURACIÓN
# ============================================================

DATASET = BASE_DIR / "Red_datasets" / "Mejorada" / "DatasetRed.csv"
OPTIMOS = BASE_DIR / "Resultados" / "Mejorada" / "01_Verificacion" / "OptimosExactos.csv"

OUTPUT_DIR = BASE_DIR / "Resultados" / "ComparacionOriginalMejorada"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ORIGEN, DESTINO = 52, 96
NUM_ABEJAS = 30
ITERACIONES = 250
SEED = 42
EPS = 1e-12


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


def evaluar_externo(G, ruta):
    """Evalúa ambas versiones con las mismas definiciones QoS."""

    latencia = jitter = 0.0
    prob_entrega = 1.0
    ancho_banda = float("inf")

    for u, v in zip(ruta[:-1], ruta[1:]):
        d = G[u][v]
        latencia += float(d["Latencia"])
        jitter += float(d["jitter"])

        p = min(max(float(d["PaquetesPerdidos"]), 0.0), 1.0)
        prob_entrega *= 1.0 - p
        ancho_banda = min(ancho_banda, float(d["AnchoBanda"]))

    return latencia, 1.0 - prob_entrega, jitter, ancho_banda


def ruta_valida(G, ruta):
    return (
        ruta
        and ruta[0] == ORIGEN
        and ruta[-1] == DESTINO
        and all(G.has_edge(u, v) for u, v in zip(ruta[:-1], ruta[1:]))
    )


def domina(a, b):
    no_peor = (
        a["Latencia"] <= b["Latencia"] + EPS
        and a["Perdida"] <= b["Perdida"] + EPS
        and a["Jitter"] <= b["Jitter"] + EPS
        and a["AnchoBanda"] >= b["AnchoBanda"] - EPS
    )

    mejor = (
        a["Latencia"] < b["Latencia"] - EPS
        or a["Perdida"] < b["Perdida"] - EPS
        or a["Jitter"] < b["Jitter"] - EPS
        or a["AnchoBanda"] > b["AnchoBanda"] + EPS
    )

    return no_peor and mejor


def reevaluar_frente(G, frente):
    """Ignora el fitness interno y vuelve a evaluar únicamente las rutas."""

    filas, vistas = [], set()

    for ruta, _ in frente:
        clave = tuple(ruta)

        if clave in vistas or not ruta_valida(G, ruta):
            continue

        vistas.add(clave)
        lat, perdida, jitter, bw = evaluar_externo(G, ruta)

        filas.append({
            "Ruta": "->".join(map(str, ruta)),
            "Saltos": len(ruta) - 1,
            "Latencia": lat,
            "Perdida": perdida,
            "Jitter": jitter,
            "AnchoBanda": bw
        })

    df = pd.DataFrame(filas)

    if df.empty:
        return df

    no_dominadas = []

    for i in range(len(df)):
        if not any(j != i and domina(df.iloc[j], df.iloc[i]) for j in range(len(df))):
            no_dominadas.append(i)

    return df.iloc[no_dominadas].reset_index(drop=True)


def ejecutar_original(G):
    # La versión original usa los generadores globales.
    random.seed(SEED)
    np.random.seed(SEED)

    inicio = time.perf_counter()
    abc = ABCOriginal(G, ORIGEN, DESTINO, NUM_ABEJAS, ITERACIONES)
    frente = abc.ejecutar()

    return frente, time.perf_counter() - inicio


def ejecutar_mejorada(G):
    inicio = time.perf_counter()

    abc = ABCMejorada(
        G, ORIGEN, DESTINO,
        num_abejas=NUM_ABEJAS,
        max_iteraciones=ITERACIONES,
        max_pareto=100,
        max_longitud_ruta=25,
        limite=60,
        seed=SEED
    )

    frente = abc.ejecutar()
    return frente, time.perf_counter() - inicio


def cargar_optimos():
    df = pd.read_csv(OPTIMOS)
    return dict(zip(df["Metrica"], df["Optimo"]))


def mejores_resultados(df):
    return {
        "Latencia": df["Latencia"].min(),
        "Perdida": df["Perdida"].min(),
        "Jitter": df["Jitter"].min(),
        "AnchoBanda": df["AnchoBanda"].max()
    }


def calcular_gap(valor, optimo, maximizar=False):
    if maximizar:
        return max(0.0, (optimo - valor) / optimo * 100)
    return max(0.0, (valor - optimo) / optimo * 100)


def comparar(df_original, df_mejorada, optimos, tiempo_original, tiempo_mejorada):
    original = mejores_resultados(df_original)
    mejorada = mejores_resultados(df_mejorada)

    filas = []

    for metrica in ["Latencia", "Perdida", "Jitter", "AnchoBanda"]:
        maximizar = metrica == "AnchoBanda"
        optimo = optimos[metrica]

        filas.append({
            "Metrica": metrica,
            "OptimoExacto": optimo,
            "Original": original[metrica],
            "Mejorada": mejorada[metrica],
            "GapOriginal": calcular_gap(original[metrica], optimo, maximizar),
            "GapMejorada": calcular_gap(mejorada[metrica], optimo, maximizar)
        })

    resumen = pd.DataFrame(filas)

    extra = pd.DataFrame([
        {
            "Version": "Original",
            "SolucionesParetoExternas": len(df_original),
            "TiempoSegundos": tiempo_original
        },
        {
            "Version": "Mejorada",
            "SolucionesParetoExternas": len(df_mejorada),
            "TiempoSegundos": tiempo_mejorada
        }
    ])

    return resumen, extra


def graficar_gaps(df):
    x = np.arange(len(df))
    ancho = 0.36

    plt.figure(figsize=(9, 5))
    plt.bar(x - ancho / 2, df["GapOriginal"], ancho, label="Original")
    plt.bar(x + ancho / 2, df["GapMejorada"], ancho, label="Mejorada")

    plt.xticks(x, df["Metrica"])
    plt.ylabel("Gap respecto al óptimo (%)")
    plt.title("Original vs. Mejorada - Seed 42")
    plt.grid(axis="y", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ComparacionGaps.png", dpi=300, bbox_inches="tight")
    plt.close()


def main():
    if not DATASET.exists():
        raise FileNotFoundError(f"No se encontró:\n{DATASET}")
    if not OPTIMOS.exists():
        raise FileNotFoundError(f"No se encontró:\n{OPTIMOS}")

    G = cargar_grafo(DATASET)
    optimos = cargar_optimos()

    print("=" * 70)
    print("COMPARACIÓN ILUSTRATIVA - ORIGINAL VS MEJORADA")
    print("=" * 70)
    print(f"Seed: {SEED} | Abejas: {NUM_ABEJAS} | Iteraciones: {ITERACIONES}\n")

    print("Ejecutando versión original...")
    frente_original, tiempo_original = ejecutar_original(G)

    print("Ejecutando versión mejorada...")
    frente_mejorada, tiempo_mejorada = ejecutar_mejorada(G)

    externo_original = reevaluar_frente(G, frente_original)
    externo_mejorada = reevaluar_frente(G, frente_mejorada)

    if externo_original.empty or externo_mejorada.empty:
        raise RuntimeError("Alguna versión no produjo rutas válidas para comparar.")

    comparacion, resumen = comparar(
        externo_original, externo_mejorada, optimos,
        tiempo_original, tiempo_mejorada
    )

    externo_original.to_csv(OUTPUT_DIR / "FrenteOriginalReevaluado.csv", index=False)
    externo_mejorada.to_csv(OUTPUT_DIR / "FrenteMejoradaReevaluado.csv", index=False)
    comparacion.to_csv(OUTPUT_DIR / "ComparacionMetricas.csv", index=False)
    resumen.to_csv(OUTPUT_DIR / "ResumenVersiones.csv", index=False)

    graficar_gaps(comparacion)

    print("\n" + "=" * 70)
    print("RESULTADOS")
    print("=" * 70)

    for _, r in comparacion.iterrows():
        print(
            f"{r['Metrica']:<12} | "
            f"Gap Original: {r['GapOriginal']:.4f}% | "
            f"Gap Mejorada: {r['GapMejorada']:.4f}%"
        )

    print()
    print(resumen.to_string(index=False))
    print(f"\nArchivos guardados en:\n{OUTPUT_DIR}")


if __name__ == "__main__":
    main()