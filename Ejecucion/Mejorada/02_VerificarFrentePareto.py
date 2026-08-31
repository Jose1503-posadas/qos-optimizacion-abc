from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DIR_VERIFICACION = BASE_DIR/"Resultados"/"Mejorada"/"01_Verificacion"
ARCHIVO_PARETO = DIR_VERIFICACION/"FrenteParetoVerificado.csv"
ARCHIVO_RESULTADO = DIR_VERIFICACION/"VerificacionFrentePareto.csv"
ARCHIVO_DOMINANCIAS = DIR_VERIFICACION/"DominanciasEncontradas.csv"
TOLERANCIA = 1e-12

def domina(a, b, eps=TOLERANCIA):
    """Comprueba dominancia Pareto: latencia, pérdida y jitter ancho de banda"""

    no_peor = (a["LatenciaABC"] <= b["LatenciaABC"] + eps and a["PerdidaABC"] <= b["PerdidaABC"] + eps and a["JitterABC"] <= b["JitterABC"] + eps and a["AnchoBandaABC"] >= b["AnchoBandaABC"] - eps)
    mejor = (a["LatenciaABC"] < b["LatenciaABC"] - eps or a["PerdidaABC"] < b["PerdidaABC"] - eps or a["JitterABC"] < b["JitterABC"] - eps or a["AnchoBandaABC"] > b["AnchoBandaABC"] + eps)

    return no_peor and mejor


def verificar_frente(df):
    """Busca dominancias y duplicados dentro del frente."""

    dominancias = []
    dominadas_por = {int(s): [] for s in df["Solucion"]}

    for i in range(len(df)):
        for j in range(len(df)):
            if i == j:
                continue

            if domina(df.iloc[i], df.iloc[j]):
                dominante = int(df.iloc[i]["Solucion"])
                dominada = int(df.iloc[j]["Solucion"])

                dominancias.append({"SolucionDominante": dominante,"SolucionDominada": dominada})
                dominadas_por[dominada].append(dominante)

    rutas_duplicadas = df["Ruta"].duplicated(keep=False)

    columnas_obj = ["LatenciaABC", "PerdidaABC", "JitterABC", "AnchoBandaABC"]
    claves_obj = df[columnas_obj].round(12).astype(str).agg("|".join, axis=1)
    objetivos_duplicados = claves_obj.duplicated(keep=False)

    resultado = df[["Solucion", "Ruta"]].copy()
    resultado["Dominada"] = resultado["Solucion"].map(lambda s: len(dominadas_por[int(s)]) > 0)
    resultado["DominadaPor"] = resultado["Solucion"].map(lambda s: ",".join(map(str, dominadas_por[int(s)])))
    resultado["RutaDuplicada"] = rutas_duplicadas.values
    resultado["ObjetivosDuplicados"] = objetivos_duplicados.values

    return resultado, pd.DataFrame(dominancias)


def mostrar_resumen(resultado, dominancias):
    total = len(resultado)
    dominadas = int(resultado["Dominada"].sum())
    rutas_dup = int(resultado["RutaDuplicada"].sum())
    objetivos_dup = int(resultado["ObjetivosDuplicados"].sum())

    print(f"Soluciones analizadas:{total}")
    print(f"Soluciones dominadas:{dominadas}")
    print(f"Rutas duplicadas:{rutas_dup}")
    print(f"Objetivos duplicados:{objetivos_dup}")

    correcto = dominadas == 0 and rutas_dup == 0 and objetivos_dup == 0

    if correcto:
        print("\nResultado: Frente")
    else:
        print("\nse encontraron inconsitencias.")

        if dominadas:
            print("\nDominancias encontradas:")
            print(dominancias.to_string(index=False))

        if rutas_dup:
            print("\nRutas duplicadas:")
            print(resultado[resultado["RutaDuplicada"]].to_string(index=False))

        if objetivos_dup:
            print("\nSoluciones con objetivos duplicados:")
            print(resultado[resultado["ObjetivosDuplicados"]].to_string(index=False))

    return correcto


def main():
    if not ARCHIVO_PARETO.exists():
        raise FileNotFoundError(
            f"No se encontró:\n{ARCHIVO_PARETO}\n"
            "Ejecuta primero 01_VerificarRutasMetricas.py."
        )

    df = pd.read_csv(ARCHIVO_PARETO)
    resultado, dominancias = verificar_frente(df)
    correcto = mostrar_resumen(resultado, dominancias)

    resultado.to_csv(ARCHIVO_RESULTADO, index=False)

    if not dominancias.empty:
        dominancias.to_csv(ARCHIVO_DOMINANCIAS, index=False)


if __name__ == "__main__":
    main()