from pathlib import Path
from itertools import combinations
import math
import random
import sys
import time
import networkx as nx
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from Algoritmo.Mejorada.AlgoritmoABC import ABCMultiobjetivo

DATASET = BASE_DIR /"Red_datasets"/"Mejorada"/"DatasetRed.csv"
OUTPUT_DIR = BASE_DIR/"Resultados"/"Mejorada"/"05_MultiplesPares"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ARCHIVO_PARES = OUTPUT_DIR/"ParesSeleccionados.csv"
ARCHIVO_OPTIMOS = OUTPUT_DIR/"OptimosPorPar.csv"
ARCHIVO_CORRIDAS = OUTPUT_DIR/"ResumenCorridas.csv"
ARCHIVO_RESUMEN = OUTPUT_DIR/"ResumenPorPar.csv"

NUM_ABEJAS = 30
MAX_ITERACIONES = 250
MAX_PARETO = 100
MAX_LONGITUD_RUTA = 25
MAX_ENLACES = MAX_LONGITUD_RUTA - 1
LIMITE = 60

SEEDS = range(1, 11)
NUM_PARES = 6
MIN_SALTOS = 2
SEED_SELECCION_PARES = 2026
PAR_REFERENCIA = (52, 96)

MIN_GRADO_ORIGEN = 2
MIN_GRADO_DESTINO = 2
TOLERANCIA = 1e-9

REANUDAR = True
REUTILIZAR_PARES = True

COLUMNAS_DATASET = {"Origen", "Destino", "AnchoBanda","Latencia", "jitter", "PaquetesPerdidos"}
METRICAS = ("Latencia", "Perdida", "Jitter", "AnchoBanda")

def cargar_grafo(archivo):
    """Carga la red dirigida con sus métricas QoS."""

    if not archivo.exists():
        raise FileNotFoundError(f"No se encontró el dataset:\n{archivo}")

    df = pd.read_csv(archivo)
    faltantes = COLUMNAS_DATASET - set(df.columns)

    if faltantes:
        raise ValueError(f"Faltan columnas en el dataset: {sorted(faltantes)}")

    G = nx.DiGraph()

    for fila in df.itertuples(index=False):
        G.add_edge(
            int(fila.Origen),
            int(fila.Destino),
            AnchoBanda=float(fila.AnchoBanda),
            Latencia=float(fila.Latencia),
            jitter=float(fila.jitter),
            PaquetesPerdidos=float(fila.PaquetesPerdidos)
        )

    return G


def seleccionar_pares(G, num_pares=NUM_PARES, seed=SEED_SELECCION_PARES):
    """Selecciona pares reproducibles con diferentes distancias mínimas."""

    rng = random.Random(seed)
    grupos = {}
    nodos = sorted(G.nodes())

    # Crear candidatos
    for i, u in enumerate(nodos):
        for v in nodos[i + 1:]:

            if G.out_degree(u) < MIN_GRADO_ORIGEN or G.in_degree(v) < MIN_GRADO_DESTINO:
                continue

            if not nx.has_path(G, u, v):
                continue

            saltos = nx.shortest_path_length(G, u, v)

            if MIN_SALTOS <= saltos <= MAX_ENLACES:
                grupos.setdefault(saltos, []).append((u, v))

    if not grupos:
        raise RuntimeError("No se encontraron pares adecuados.")

    for candidatos in grupos.values():
        rng.shuffle(candidatos)

    seleccionados = []

    # Agrega un par y decide su dirección
    def agregar_par(u, v, tipo):
        origen, destino = (u, v) if rng.random() < 0.5 else (v, u)

        if not nx.has_path(G, origen, destino):
            origen, destino = u, v

        seleccionados.append({"Origen": origen,"Destino": destino, "SaltosMinimos": nx.shortest_path_length(G, origen, destino),"Tipo": tipo})

    # Agregar primero el par utilizado como referencia
    origen_ref, destino_ref = PAR_REFERENCIA

    if origen_ref in G and destino_ref in G and nx.has_path(G, origen_ref, destino_ref):

        seleccionados.append({"Origen": origen_ref,"Destino": destino_ref,"SaltosMinimos": nx.shortest_path_length(G, origen_ref, destino_ref),"Tipo": "Referencia"})
        clave_ref = tuple(sorted(PAR_REFERENCIA))

        for saltos in grupos:
            grupos[saltos] = [
                par for par in grupos[saltos]
                if tuple(sorted(par)) != clave_ref
            ]

    # Intentar representar diferentes distancias
    niveles = sorted(grupos)
    niveles_representados = {par["SaltosMinimos"] for par in seleccionados}

    for saltos in niveles:

        if len(seleccionados) >= num_pares:
            break

        if saltos not in niveles_representados and grupos[saltos]:
            agregar_par(*grupos[saltos].pop(), "Adicional")
            niveles_representados.add(saltos)

    # Completar los pares faltantes
    while len(seleccionados) < num_pares:

        agregado = False

        for saltos in niveles:
            if len(seleccionados) >= num_pares:
                break
            if grupos[saltos]:
                agregar_par(*grupos[saltos].pop(), "Adicional")
                agregado = True

        if not agregado:
            break

    if len(seleccionados) < num_pares:
        print(f"\n sólo se encontraron {len(seleccionados)} pares adecuados.\n")

    # Agregar información topológica
    for i, par in enumerate(seleccionados, 1):

        origen, destino = par["Origen"], par["Destino"]

        par.update({
            "Par": f"P{i:02d}",
            "GradoSalidaOrigen": G.out_degree(origen),
            "GradoEntradaDestino": G.in_degree(destino)
        })

    columnas = ["Par", "Origen", "Destino", "SaltosMinimos","GradoSalidaOrigen", "GradoEntradaDestino", "Tipo"]

    return pd.DataFrame(seleccionados)[columnas]


def obtener_pares(G):
    """Reutiliza los pares existentes o genera nuevos."""

    if REUTILIZAR_PARES and ARCHIVO_PARES.exists():
        print("Reutilizando pares ya seleccionados...")
        return pd.read_csv(ARCHIVO_PARES)

    df = seleccionar_pares(G)
    df.to_csv(ARCHIVO_PARES, index=False)

    return df

def reconstruir(pred, destino, h):
    ruta, actual = [destino], destino

    while h > 0:
        actual = pred[h][actual]
        ruta.append(actual)
        h -= 1

    return ruta[::-1]


def quitar_ciclos(ruta):
    salida, posiciones = [], {}

    for nodo in ruta:

        if nodo in posiciones:
            salida = salida[:posiciones[nodo] + 1]
            posiciones = {n: i for i, n in enumerate(salida)}

        else:
            posiciones[nodo] = len(salida)
            salida.append(nodo)

    return salida


def _optimo_dp(G, origen, destino, inicial, defecto, combinar, mejor, elegir, alcanzable):

    nodos = list(G.nodes)
    dp = [{nodo: defecto for nodo in nodos} for _ in range(MAX_ENLACES + 1)]
    pred = [{} for _ in range(MAX_ENLACES + 1)]

    dp[0][origen] = inicial

    for h in range(1, MAX_ENLACES + 1):
        for u, v, datos in G.edges(data=True):
            anterior = dp[h - 1][u]
            if not alcanzable(anterior):
                continue

            nuevo = combinar(anterior, datos)
            if mejor(nuevo, dp[h][v]):
                dp[h][v] = nuevo
                pred[h][v] = u

    h_mejor = elegir(
        range(1, MAX_ENLACES + 1),
        key=lambda h: dp[h][destino]
    )

    if not alcanzable(dp[h_mejor][destino]):
        raise ValueError(f"No existe ruta válida {origen}->{destino}.")

    ruta = reconstruir(pred, destino, h_mejor)

    return dp[h_mejor][destino], quitar_ciclos(ruta)


def optimo_aditivo(G, origen, destino, atributo):

    return _optimo_dp(G,origen,destino,0.0,math.inf,lambda anterior, datos: anterior + float(datos[atributo]),lambda nuevo, actual: nuevo < actual,min,lambda valor: not math.isinf(valor))


def optimo_perdida(G, origen, destino):

    entrega, ruta = _optimo_dp(
        G,
        origen,
        destino,
        1.0,
        -1.0,
        lambda anterior, datos:
            anterior * (1.0 - min(max(float(datos["PaquetesPerdidos"]), 0.0), 1.0)),
        lambda nuevo, actual: nuevo > actual,
        max,
        lambda valor: valor >= 0
    )

    return 1.0 - entrega, ruta


def optimo_ancho_banda(G, origen, destino):
    return _optimo_dp(G,origen,destino,math.inf,-1.0,lambda anterior, datos: min(anterior, float(datos["AnchoBanda"])),lambda nuevo, actual: nuevo > actual,max,lambda valor: valor >= 0)


def calcular_optimos(G, origen, destino):

    latencia, ruta_latencia = optimo_aditivo(G, origen, destino, "Latencia")
    perdida, ruta_perdida = optimo_perdida(G, origen, destino)
    jitter, ruta_jitter = optimo_aditivo(G, origen, destino, "jitter")
    ancho_banda, ruta_bw = optimo_ancho_banda(G, origen, destino)

    valores = {"Latencia": (latencia, ruta_latencia),"Perdida": (perdida, ruta_perdida),"Jitter": (jitter, ruta_jitter),"AnchoBanda": (ancho_banda, ruta_bw)}
    resultado = {}

    for nombre, (valor, ruta) in valores.items():

        resultado[f"Optimo{nombre}"] = valor
        resultado[f"RutaOptima{nombre}"] = "->".join(map(str, ruta))
        resultado[f"SaltosOptimo{nombre}"] = len(ruta) - 1

    return resultado

def evaluar_ruta(G, ruta):
    """Calcula externamente las cuatro métricas QoS."""

    latencia = jitter = 0.0
    prob_entrega, ancho_banda = 1.0, math.inf

    for u, v in zip(ruta[:-1], ruta[1:]):

        datos = G[u][v]

        latencia += float(datos["Latencia"])
        jitter += float(datos["jitter"])

        perdida = min(max(float(datos["PaquetesPerdidos"]), 0.0), 1.0)
        prob_entrega *= 1.0 - perdida

        ancho_banda = min(ancho_banda, float(datos["AnchoBanda"]))

    return latencia, 1.0 - prob_entrega, jitter, ancho_banda


def ruta_valida(G, ruta, origen, destino):

    return (
        bool(ruta)
        and ruta[0] == origen
        and ruta[-1] == destino
        and len(ruta) <= MAX_LONGITUD_RUTA
        and len(ruta) == len(set(ruta))
        and all(G.has_edge(u, v) for u, v in zip(ruta[:-1], ruta[1:]))
    )


def diversidad_rutas(rutas):

    enlaces = [set(zip(ruta[:-1], ruta[1:])) for ruta in rutas]

    distancias = [1.0 - len(a & b) / len(a | b) if a | b else 0.0 for a, b in combinations(enlaces, 2)]

    return float(np.mean(distancias)) if distancias else 0.0

def gap(valor, optimo, minimizar=True):

    if math.isclose(optimo, 0.0, abs_tol=1e-15):
        return (0.0 if math.isclose(valor,optimo,rel_tol=TOLERANCIA, abs_tol=TOLERANCIA) else math.inf)

    resultado = ((valor - optimo)/optimo * 100 if minimizar else (optimo - valor) / optimo * 100)

    return max(0.0, resultado)


def construir_dataframe_frente(G, frente, origen, destino):
    filas, vistas = [], set()

    for i, (ruta, _) in enumerate(frente, 1):

        clave = tuple(ruta)
        if clave in vistas or not ruta_valida(G, ruta, origen, destino):
            continue

        vistas.add(clave)
        latencia, perdida, jitter, bw = evaluar_ruta(G, ruta)

        filas.append({
            "Solucion": i,
            "Ruta": "->".join(map(str, ruta)),
            "Saltos": len(ruta) - 1,
            "Latencia": latencia,
            "Perdida": perdida,
            "Jitter": jitter,
            "AnchoBanda": bw
        })

    return pd.DataFrame(filas)


def guardar_ejecucion(par_id, origen, destino, seed, abc, df_frente):

    carpeta = OUTPUT_DIR / f"{par_id}_{origen}_{destino}" / f"Seed_{seed:02d}"
    carpeta.mkdir(parents=True, exist_ok=True)

    df_frente.to_csv(carpeta / "FrentePareto.csv", index=False)
    pd.DataFrame(abc.historial).to_csv(carpeta / "HistorialABC.csv", index=False)


def ejecutar_seed(G, par, optimos, seed):

    par_id = par["Par"]
    origen, destino = int(par["Origen"]), int(par["Destino"])

    inicio = time.perf_counter()

    abc = ABCMultiobjetivo(
        G,
        origen,
        destino,
        num_abejas=NUM_ABEJAS,
        max_iteraciones=MAX_ITERACIONES,
        max_pareto=MAX_PARETO,
        max_longitud_ruta=MAX_LONGITUD_RUTA,
        limite=LIMITE,
        seed=seed
    )

    frente = abc.ejecutar()
    tiempo = time.perf_counter() - inicio

    if not frente:
        raise RuntimeError("El algoritmo no produjo un frente de Pareto.")

    df_frente = construir_dataframe_frente(G, frente, origen, destino)

    if df_frente.empty:
        raise RuntimeError("El frente no contiene rutas válidas.")

    guardar_ejecucion(par_id, origen, destino, seed, abc, df_frente)

    mejores = {
        "Latencia": float(df_frente["Latencia"].min()),
        "Perdida": float(df_frente["Perdida"].min()),
        "Jitter": float(df_frente["Jitter"].min()),
        "AnchoBanda": float(df_frente["AnchoBanda"].max())
    }

    alcanzados = {
        nombre: math.isclose(
            mejores[nombre],
            optimos[f"Optimo{nombre}"],
            rel_tol=TOLERANCIA,
            abs_tol=TOLERANCIA
        )
        for nombre in METRICAS
    }

    final = abc.historial[-1] if abc.historial else {}

    resultado = {
        "Par": par_id,
        "Origen": origen,
        "Destino": destino,
        "SaltosMinimos": int(par["SaltosMinimos"]),
        "Seed": seed,
        "Estado": "OK",
        "TiempoSegundos": tiempo,
        "TamanoPareto": len(df_frente),
        "PoblacionUnica": final.get(
            "PoblacionUnica",
            len({tuple(ruta) for ruta in abc.poblacion})
        ),
        "DiversidadPoblacion": final.get("DiversidadRutas", np.nan),
        "DiversidadFrente": diversidad_rutas([ruta for ruta, _ in frente])
    }

    for nombre in METRICAS:

        resultado[f"Mejor{nombre}"] = mejores[nombre]

        resultado[f"Gap{nombre}"] = gap(
            mejores[nombre],
            optimos[f"Optimo{nombre}"],
            minimizar=nombre != "AnchoBanda"
        )

        resultado[f"Optimo{nombre}"] = alcanzados[nombre]

    resultado["OptimosAlcanzados"] = sum(alcanzados.values())
    resultado["TodosOptimos"] = all(alcanzados.values())

    return resultado

def calcular_optimos_pares(G, df_pares):

    filas = []

    for _, par in df_pares.iterrows():

        par_id = par["Par"]
        origen, destino = int(par["Origen"]), int(par["Destino"])

        print(f"{par_id}: {origen}->{destino}...", end=" ", flush=True)

        filas.append({
            "Par": par_id,
            "Origen": origen,
            "Destino": destino,
            "SaltosMinimos": int(par["SaltosMinimos"]),
            **calcular_optimos(G, origen, destino)
        })
    df = pd.DataFrame(filas)
    df.to_csv(ARCHIVO_OPTIMOS, index=False)

    return df

def generar_resumen_por_par(df_corridas, df_pares, df_optimos):

    promedios = {
        "TiempoPromedio": "TiempoSegundos",
        "ParetoPromedio": "TamanoPareto",
        "DiversidadFrentePromedio": "DiversidadFrente",
        "GapLatenciaPromedio": "GapLatencia",
        "GapPerdidaPromedio": "GapPerdida",
        "GapJitterPromedio": "GapJitter",
        "GapAnchoBandaPromedio": "GapAnchoBanda"
    }

    maximos = {
        "GapLatenciaMaximo": "GapLatencia",
        "GapPerdidaMaximo": "GapPerdida",
        "GapJitterMaximo": "GapJitter",
        "GapAnchoBandaMaximo": "GapAnchoBanda"
    }

    exitos = {
        "ExitoLatenciaPct": "OptimoLatencia",
        "ExitoPerdidaPct": "OptimoPerdida",
        "ExitoJitterPct": "OptimoJitter",
        "ExitoAnchoBandaPct": "OptimoAnchoBanda",
        "ExitoCompletoPct": "TodosOptimos"
    }

    campos_estadisticos = (
        list(promedios)
        + list(maximos)
        + list(exitos)
        + ["OptimosPromedio"]
    )

    filas = []

    for _, par in df_pares.iterrows():

        par_id = par["Par"]

        sub = df_corridas[
            (df_corridas["Par"] == par_id)
            & (df_corridas["Estado"] == "OK")
        ]

        opt = df_optimos[df_optimos["Par"] == par_id].iloc[0]

        fila = {
            "Par": par_id,
            "Origen": int(par["Origen"]),
            "Destino": int(par["Destino"]),
            "SaltosMinimos": int(par["SaltosMinimos"]),
            "GradoSalidaOrigen": int(par["GradoSalidaOrigen"]),
            "GradoEntradaDestino": int(par["GradoEntradaDestino"]),
            "CorridasEsperadas": len(SEEDS),
            "CorridasCompletadas": len(sub),
            **{f"Optimo{m}": opt[f"Optimo{m}"] for m in METRICAS}
        }

        if sub.empty:

            fila.update({campo: np.nan for campo in campos_estadisticos})

        else:

            fila.update({
                salida: sub[columna].mean()
                for salida, columna in promedios.items()
            })

            fila.update({
                salida: sub[columna].max()
                for salida, columna in maximos.items()
            })

            fila.update({
                salida: sub[columna].mean() * 100
                for salida, columna in exitos.items()
            })

            fila["OptimosPromedio"] = sub["OptimosAlcanzados"].mean()

        filas.append(fila)

    return pd.DataFrame(filas)


def mostrar_resumen(df_resumen):
    campos = [
        ("Pareto promedio", "ParetoPromedio", ".2f", ""),
        ("Tiempo promedio", "TiempoPromedio", ".2f", " s"),
        ("Diversidad promedio", "DiversidadFrentePromedio", ".4f", ""),
        ("Éxito latencia", "ExitoLatenciaPct", ".2f", "%"),
        ("Éxito pérdida", "ExitoPerdidaPct", ".2f", "%"),
        ("Éxito jitter", "ExitoJitterPct", ".2f", "%"),
        ("Éxito ancho de banda", "ExitoAnchoBandaPct", ".2f", "%"),
        ("Éxito completo", "ExitoCompletoPct", ".2f", "%")
    ]

    for _, fila in df_resumen.iterrows():

        print(f"\n{fila['Par']} | {int(fila['Origen'])}->{int(fila['Destino'])}")
        print(f"  Saltos mínimos:           {int(fila['SaltosMinimos'])}")
        print(
            f"  Corridas completadas:     "
            f"{int(fila['CorridasCompletadas'])}/{int(fila['CorridasEsperadas'])}"
        )

        for etiqueta, columna, formato, sufijo in campos:
            valor = format(fila[columna], formato)
            print(f"  {etiqueta + ':':28} {valor}{sufijo}")

    validos = df_resumen[df_resumen["CorridasCompletadas"] > 0]

    if validos.empty:
        return

    globales = [
        ("Éxito completo promedio", "ExitoCompletoPct", "%"),
        ("Éxito promedio latencia", "ExitoLatenciaPct", "%"),
        ("Éxito promedio pérdida", "ExitoPerdidaPct", "%"),
        ("Éxito promedio jitter", "ExitoJitterPct", "%"),
        ("Éxito promedio ancho de banda", "ExitoAnchoBandaPct", "%"),
        ("Pareto promedio global", "ParetoPromedio", ""),
        ("Tiempo promedio global", "TiempoPromedio", " s")
    ]

    for etiqueta, columna, sufijo in globales:
        print(f"{etiqueta + ':':32} {validos[columna].mean():.2f}{sufijo}")


def actualizar_resultados(resultados, par_id, seed, nuevo):

    resultados = [
        r for r in resultados
        if not (
            r.get("Par") == par_id
            and int(r.get("Seed", -1)) == seed
        )
    ]

    resultados.append(nuevo)

    return resultados


def main():

    print("=" * 90)
    print("EXPERIMENTO - MÚLTIPLES PARES ORIGEN-DESTINO")
    print("=" * 90)

    print(
        f"Abejas: {NUM_ABEJAS} | "
        f"Iteraciones: {MAX_ITERACIONES} | "
        f"Pares: {NUM_PARES} | "
        f"Seeds/par: {len(SEEDS)} | "
        f"Corridas: {NUM_PARES * len(SEEDS)}"
    )

    # Cargar red
    G = cargar_grafo(DATASET)

    print(f"\nRed cargada: " f"{G.number_of_nodes()} nodos | " f"{G.number_of_edges()} enlaces")

    # Seleccionar pares
    df_pares = obtener_pares(G)

    # Calcular óptimos
    df_optimos = calcular_optimos_pares(G, df_pares)
    optimos_por_par = {
        fila["Par"]: fila.to_dict()
        for _, fila in df_optimos.iterrows()
    }

    # Recuperar ejecuciones anteriores
    resultados, completados = [], set()

    if REANUDAR and ARCHIVO_CORRIDAS.exists():

        df_anterior = pd.read_csv(ARCHIVO_CORRIDAS)
        resultados = df_anterior.to_dict("records")

        completados = {
            (fila["Par"], int(fila["Seed"]))
            for _, fila in df_anterior.iterrows()
            if fila.get("Estado") == "OK"
        }

        print(f"\nSe encontraron {len(completados)} corridas ya terminadas.")

    # Ejecutar experimento
    total = len(df_pares) * len(SEEDS)
    contador = 0

    for _, par in df_pares.iterrows():

        par_id = par["Par"]
        origen, destino = int(par["Origen"]), int(par["Destino"])
        optimos = optimos_por_par[par_id]

        print("\n" + "=" * 90)
        print(
            f"{par_id}: {origen}->{destino} | "
            f"{int(par['SaltosMinimos'])} saltos mínimos"
        )
        print("=" * 90)

        for seed in SEEDS:

            contador += 1
            clave = (par_id, seed)

            if clave in completados:
                print(
                    f"[{contador:02d}/{total}] "
                    f"{par_id} | Seed {seed:02d} "
                    "→ ya realizada"
                )
                continue

            print(
                f"[{contador:02d}/{total}] "
                f"{par_id} | Seed {seed:02d}...",
                end=" ",
                flush=True
            )

            try:
                nuevo = ejecutar_seed(G, par, optimos, seed)
                resultados = actualizar_resultados(resultados, par_id, seed, nuevo)

                print(f"Pareto={nuevo['TamanoPareto']} | " f"Óptimos={nuevo['OptimosAlcanzados']}/4 | " f"{nuevo['TiempoSegundos']:.1f}s")

            except Exception as error:

                print(f"{error}")

                nuevo = {
                    "Par": par_id,
                    "Origen": origen,
                    "Destino": destino,
                    "SaltosMinimos": int(par["SaltosMinimos"]),
                    "Seed": seed,
                    "Estado": "ERROR",
                    "Error": str(error)
                }

                resultados = actualizar_resultados(resultados, par_id, seed, nuevo)

            # Guardar después de cada ejecución
            pd.DataFrame(resultados).to_csv(ARCHIVO_CORRIDAS, index=False)

    # Generar resumen final
    df_corridas = pd.DataFrame(resultados)
    df_corridas.to_csv(ARCHIVO_CORRIDAS, index=False)

    df_resumen = generar_resumen_por_par(df_corridas, df_pares, df_optimos)
    df_resumen.to_csv(ARCHIVO_RESUMEN, index=False)

    mostrar_resumen(df_resumen)

if __name__ == "__main__":
    main()