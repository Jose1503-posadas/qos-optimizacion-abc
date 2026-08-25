from pathlib import Path
import math
import sys
import networkx as nx
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from Algoritmo.Mejorada.AlgoritmoABC import ABCMultiobjetivo

DATASET = BASE_DIR/"Red_datasets"/"Mejorada"/"DatasetRed.csv"
OUTPUT_DIR = BASE_DIR/"Resultados"/"Mejorada"/"01_Verificacion"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVO_VERIFICACION = OUTPUT_DIR/"VerificacionRutasMetricas.csv"
ARCHIVO_PARETO = OUTPUT_DIR/"FrenteParetoVerificado.csv"
ORIGEN, DESTINO = 52, 96
NUM_ABEJAS = 30
MAX_ITERACIONES = 100
MAX_PARETO = 100
MAX_LONGITUD_RUTA = 25
LIMITE = 60
SEED = 42
TOLERANCIA = 1e-9


def cargar_grafo(archivo_csv):
    """Carga el grafo dirigido desde el dataset."""

    if not archivo_csv.exists():
        raise FileNotFoundError(f"No se encontró el dataset:\n{archivo_csv}")

    df = pd.read_csv(archivo_csv)
    requeridas = {"Origen", "Destino", "AnchoBanda", "Latencia", "jitter", "PaquetesPerdidos"}
    faltantes = requeridas - set(df.columns)

    if faltantes:
        raise ValueError(f"Faltan columnas en el CSV: {sorted(faltantes)}")

    G = nx.DiGraph()

    for _, f in df.iterrows():
        G.add_edge(int(f["Origen"]), int(f["Destino"]), AnchoBanda=float(f["AnchoBanda"]), Latencia=float(f["Latencia"]), jitter=float(f["jitter"]), PaquetesPerdidos=float(f["PaquetesPerdidos"]))

    return G


def verificar_ruta(G, ruta, origen, destino, max_longitud):
    """Comprueba la estructura de una ruta sin usar la validación del ABC."""

    if not ruta:
        return False, ["Ruta vacía"]

    errores = []

    if ruta[0] != origen:
        errores.append("Origen incorrecto")
    if ruta[-1] != destino:
        errores.append("Destino incorrecto")
    if len(ruta) > max_longitud:
        errores.append("Supera la longitud máxima")
    if len(ruta) != len(set(ruta)):
        errores.append("Contiene nodos repetidos")

    errores += [
        f"No existe el enlace {u}->{v}"
        for u, v in zip(ruta[:-1], ruta[1:])
        if not G.has_edge(u, v)
    ]

    return not errores, errores


def recalcular_metricas(G, ruta):
    """Recalcula las métricas QoS directamente desde las aristas."""

    latencia = jitter = 0.0
    prob_entrega = 1.0
    ancho_banda = float("inf")

    for u, v in zip(ruta[:-1], ruta[1:]):
        d = G[u][v]
        latencia += float(d["Latencia"])
        jitter += float(d["jitter"])

        perdida = min(max(float(d["PaquetesPerdidos"]), 0.0), 1.0)
        prob_entrega *= 1.0 - perdida
        ancho_banda = min(ancho_banda, float(d["AnchoBanda"]))

    return {"Latencia": latencia,"Perdida": 1.0 - prob_entrega,"Jitter": jitter,"AnchoBanda": ancho_banda}


def verificar_frente_metricas(G, abc, frente, tolerancia=TOLERANCIA):
    """Valida rutas y compara el fitness del ABC con un cálculo independiente."""

    resultados, filas_pareto = [], []

    for i, (ruta, fitness) in enumerate(frente, start=1):
        valida, errores = verificar_ruta(G, ruta, abc.origen, abc.destino, abc.MAX_LONGITUD_RUTA)
        recalculadas = recalcular_metricas(G, ruta)

        valores_abc = {"Latencia": float(fitness[0]),"Perdida": float(fitness[1]),"Jitter": float(fitness[2]),"AnchoBanda": float(-fitness[3])}

        correctas = {
            nombre: math.isclose(valores_abc[nombre], recalculadas[nombre], rel_tol=0.0, abs_tol=tolerancia)
            for nombre in valores_abc
        }

        resultados.append({
            "Solucion": i,
            "RutaValida": valida,
            "LatenciaCorrecta": correctas["Latencia"],
            "PerdidaCorrecta": correctas["Perdida"],
            "JitterCorrecto": correctas["Jitter"],
            "AnchoBandaCorrecto": correctas["AnchoBanda"],
            "MetricasCorrectas": all(correctas.values()),
            "ErroresRuta": ", ".join(errores)
        })

        fila = {"Solucion": i, "Ruta": "->".join(map(str, ruta)), "Saltos": len(ruta) - 1}

        for nombre in valores_abc:
            fila[f"{nombre}ABC"] = valores_abc[nombre]
            fila[f"{nombre}Recalculado"] = recalculadas[nombre]
            fila[f"Diferencia{nombre}"] = abs(valores_abc[nombre] - recalculadas[nombre])

        filas_pareto.append(fila)

    return pd.DataFrame(resultados), pd.DataFrame(filas_pareto)


def mostrar_resumen(df):
    """Muestra el resultado general de la verificación."""

    total = len(df)
    print(f"Soluciones Pareto:              {total}")
    print(f"Rutas válidas:                  {df['RutaValida'].sum()}/{total}")
    print(f"Latencias correctas:            {df['LatenciaCorrecta'].sum()}/{total}")
    print(f"Pérdidas correctas:             {df['PerdidaCorrecta'].sum()}/{total}")
    print(f"Jitters correctos:              {df['JitterCorrecto'].sum()}/{total}")
    print(f"Anchos de banda correctos:      {df['AnchoBandaCorrecto'].sum()}/{total}")
    print(f"Fitness completamente correcto: {df['MetricasCorrectas'].sum()}/{total}")

    correcto = df["RutaValida"].all() and df["MetricasCorrectas"].all()

    if not correcto:
        errores = df[(~df["RutaValida"]) | (~df["MetricasCorrectas"])]
        print("\nSoluciones con problemas:")
        print(errores.to_string(index=False))

    return correcto


def main():
    print(f"Origen: {ORIGEN} | Destino: {DESTINO} | Abejas: {NUM_ABEJAS}")
    print(f"Iteraciones: {MAX_ITERACIONES} | Seed: {SEED}\n")

    G = cargar_grafo(DATASET)

    if ORIGEN not in G or DESTINO not in G:
        raise ValueError("Origen o destino no existen en el grafo.")
    if not nx.has_path(G, ORIGEN, DESTINO):
        raise ValueError(f"No existe ruta entre {ORIGEN} y {DESTINO}.")

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
    df_verificacion, df_pareto = verificar_frente_metricas(G, abc, frente)
    correcto = mostrar_resumen(df_verificacion)
    df_verificacion.to_csv(ARCHIVO_VERIFICACION, index=False)
    df_pareto.to_csv(ARCHIVO_PARETO, index=False)


if __name__ == "__main__":
    main()