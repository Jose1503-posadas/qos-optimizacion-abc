from pathlib import Path
import math
import networkx as nx
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATASET = BASE_DIR/"Red_datasets"/"Mejorada"/"DatasetRed.csv"
DIR_RESULTADOS = BASE_DIR/"Resultados"/"Mejorada"/"01_Verificacion"
ARCHIVO_PARETO = DIR_RESULTADOS/"FrenteParetoVerificado.csv"
ARCHIVO_OPTIMOS = DIR_RESULTADOS/"OptimosExactos.csv"
ARCHIVO_COMPARACION = DIR_RESULTADOS/"ComparacionABCExactos.csv"
ORIGEN, DESTINO = 52, 96
MAX_LONGITUD_RUTA = 25
MAX_ENLACES = MAX_LONGITUD_RUTA - 1
TOLERANCIA = 1e-9


def cargar_grafo(archivo):
    df = pd.read_csv(archivo)
    G = nx.DiGraph()

    for _, f in df.iterrows():
        G.add_edge(int(f["Origen"]), int(f["Destino"]),Latencia=float(f["Latencia"]),PaquetesPerdidos=float(f["PaquetesPerdidos"]),jitter=float(f["jitter"]),AnchoBanda=float(f["AnchoBanda"]))
    return G


def reconstruir(pred, destino, h):
    ruta, actual = [destino], destino

    while h > 0:
        actual = pred[h][actual]
        ruta.append(actual)
        h -= 1

    return ruta[::-1]


def quitar_ciclos(ruta):
    """Elimina ciclos si una solución óptima contiene un nodo repetido."""
    salida, posiciones = [], {}

    for nodo in ruta:
        if nodo in posiciones:
            pos = posiciones[nodo]
            salida = salida[:pos + 1]
            posiciones = {n: i for i, n in enumerate(salida)}
        else:
            posiciones[nodo] = len(salida)
            salida.append(nodo)

    return salida


def optimo_aditivo(G, atributo):
    """Óptimo exacto con máximo MAX_ENLACES para una métrica aditiva."""
    nodos = list(G.nodes)
    dp = [{n: math.inf for n in nodos} for _ in range(MAX_ENLACES + 1)]
    pred = [{} for _ in range(MAX_ENLACES + 1)]
    dp[0][ORIGEN] = 0.0

    for h in range(1, MAX_ENLACES + 1):
        for u, v, d in G.edges(data=True):
            if math.isinf(dp[h - 1][u]):
                continue

            nuevo = dp[h - 1][u] + float(d[atributo])
            if nuevo < dp[h][v]:
                dp[h][v], pred[h][v] = nuevo, u

    h_mejor = min(range(1, MAX_ENLACES + 1), key=lambda h: dp[h][DESTINO])

    if math.isinf(dp[h_mejor][DESTINO]):
        raise ValueError(f"No se encontró ruta para {atributo}.")

    ruta = quitar_ciclos(reconstruir(pred, DESTINO, h_mejor))
    return dp[h_mejor][DESTINO], ruta


def optimo_perdida(G):
    """Minimiza pérdida maximizando la probabilidad de entrega."""
    nodos = list(G.nodes)
    dp = [{n: -1.0 for n in nodos} for _ in range(MAX_ENLACES + 1)]
    pred = [{} for _ in range(MAX_ENLACES + 1)]
    dp[0][ORIGEN] = 1.0

    for h in range(1, MAX_ENLACES + 1):
        for u, v, d in G.edges(data=True):
            if dp[h - 1][u] < 0:
                continue

            p = min(max(float(d["PaquetesPerdidos"]), 0.0), 1.0)
            entrega = dp[h - 1][u] * (1.0 - p)

            if entrega > dp[h][v]:
                dp[h][v], pred[h][v] = entrega, u

    h_mejor = max(range(1, MAX_ENLACES + 1), key=lambda h: dp[h][DESTINO])
    ruta = quitar_ciclos(reconstruir(pred, DESTINO, h_mejor))
    return 1.0 - dp[h_mejor][DESTINO], ruta


def optimo_ancho_banda(G):
    """Maximiza el ancho de banda cuello de botella."""
    nodos = list(G.nodes)
    dp = [{n: -1.0 for n in nodos} for _ in range(MAX_ENLACES + 1)]
    pred = [{} for _ in range(MAX_ENLACES + 1)]
    dp[0][ORIGEN] = math.inf

    for h in range(1, MAX_ENLACES + 1):
        for u, v, d in G.edges(data=True):
            if dp[h - 1][u] < 0:
                continue

            bw = min(dp[h - 1][u], float(d["AnchoBanda"]))

            if bw > dp[h][v]:
                dp[h][v], pred[h][v] = bw, u

    h_mejor = max(range(1, MAX_ENLACES + 1), key=lambda h: dp[h][DESTINO])
    ruta = quitar_ciclos(reconstruir(pred, DESTINO, h_mejor))
    return dp[h_mejor][DESTINO], ruta


def calcular_optimos(G):
    lat, ruta_lat = optimo_aditivo(G, "Latencia")
    jit, ruta_jit = optimo_aditivo(G, "jitter")
    perdida, ruta_perdida = optimo_perdida(G)
    bw, ruta_bw = optimo_ancho_banda(G)

    return pd.DataFrame([
        {"Metrica": "Latencia", "Optimo": lat, "Ruta": "->".join(map(str, ruta_lat)), "Saltos": len(ruta_lat) - 1},
        {"Metrica": "Perdida", "Optimo": perdida, "Ruta": "->".join(map(str, ruta_perdida)), "Saltos": len(ruta_perdida) - 1},
        {"Metrica": "Jitter", "Optimo": jit, "Ruta": "->".join(map(str, ruta_jit)), "Saltos": len(ruta_jit) - 1},
        {"Metrica": "AnchoBanda", "Optimo": bw, "Ruta": "->".join(map(str, ruta_bw)), "Saltos": len(ruta_bw) - 1},
    ])


def comparar_con_abc(df_pareto, df_optimos):
    columnas = {"Latencia": ("LatenciaABC", "min"),"Perdida": ("PerdidaABC", "min"),"Jitter": ("JitterABC", "min"),"AnchoBanda": ("AnchoBandaABC", "max")}
    filas = []

    for _, opt in df_optimos.iterrows():
        metrica = opt["Metrica"]
        columna, tipo = columnas[metrica]

        idx = df_pareto[columna].idxmin() if tipo == "min" else df_pareto[columna].idxmax()
        mejor_abc = float(df_pareto.loc[idx, columna])
        exacto = float(opt["Optimo"])

        gap = ((mejor_abc - exacto) / exacto * 100) if tipo == "min" else ((exacto - mejor_abc) / exacto * 100)
        gap = max(0.0, gap)

        filas.append({
            "Metrica": metrica,
            "OptimoExacto": exacto,
            "MejorABC": mejor_abc,
            "GapPorcentaje": gap,
            "OptimoAlcanzado": math.isclose(mejor_abc, exacto, rel_tol=TOLERANCIA, abs_tol=TOLERANCIA),
            "RutaExacta": opt["Ruta"],
            "RutaABC": df_pareto.loc[idx, "Ruta"]
        })

    return pd.DataFrame(filas)


def main():
    if not DATASET.exists():
        raise FileNotFoundError(f"No se encontró:\n{DATASET}")
    if not ARCHIVO_PARETO.exists():
        raise FileNotFoundError(f"No se encontró:\n{ARCHIVO_PARETO}")

    G = cargar_grafo(DATASET)
    df_pareto = pd.read_csv(ARCHIVO_PARETO)

    df_optimos = calcular_optimos(G)
    df_comparacion = comparar_con_abc(df_pareto, df_optimos)

    for _, r in df_comparacion.iterrows():
        estado = "SI" if r["OptimoAlcanzado"] else "NO"
        print(
            f"{r['Metrica']:<12} | Exacto: {r['OptimoExacto']:.10f} "
            f"| ABC: {r['MejorABC']:.10f} | Gap: {r['GapPorcentaje']:.6f}% "
            f"| Óptimo: {estado}"
        )

    df_optimos.to_csv(ARCHIVO_OPTIMOS, index=False)
    df_comparacion.to_csv(ARCHIVO_COMPARACION, index=False)


if __name__ == "__main__":
    main()