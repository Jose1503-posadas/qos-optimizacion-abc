from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

CORRIDAS_DIR = BASE_DIR / "Resultados" / "Mejorada" / "03_MultiplesSemillas"
OUTPUT_DIR = BASE_DIR / "Resultados" / "Mejorada" / "05_FrenteReferencia"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ARCHIVO_TODAS = OUTPUT_DIR / "SolucionesCombinadas.csv"
ARCHIVO_REFERENCIA = OUTPUT_DIR / "FrenteParetoReferencia.csv"
ARCHIVO_RESUMEN = OUTPUT_DIR / "ResumenFrenteReferencia.csv"

SEEDS = range(1, 31)
EPS = 1e-12


def domina(a, b, eps=EPS):
    """Latencia, pérdida y jitter se minimizan; ancho de banda se maximiza."""

    no_peor = (
        a["Latencia"] <= b["Latencia"] + eps
        and a["Perdida"] <= b["Perdida"] + eps
        and a["Jitter"] <= b["Jitter"] + eps
        and a["AnchoBanda"] >= b["AnchoBanda"] - eps
    )

    mejor = (
        a["Latencia"] < b["Latencia"] - eps
        or a["Perdida"] < b["Perdida"] - eps
        or a["Jitter"] < b["Jitter"] - eps
        or a["AnchoBanda"] > b["AnchoBanda"] + eps
    )

    return no_peor and mejor


def cargar_soluciones():
    """Combina los frentes Pareto de las 30 semillas."""

    datos = []

    for seed in SEEDS:
        archivo = CORRIDAS_DIR / f"Seed_{seed:02d}" / "FrentePareto.csv"

        if not archivo.exists():
            raise FileNotFoundError(f"No se encontró:\n{archivo}")

        df = pd.read_csv(archivo)
        df["Seed"] = seed
        datos.append(df)

    return pd.concat(datos, ignore_index=True)


def eliminar_duplicados(df):
    """Elimina rutas repetidas y soluciones con los mismos objetivos."""

    total_inicial = len(df)

    # Conserva una sola aparición de cada ruta y registra en qué seeds apareció
    semillas_ruta = (
        df.groupby("Ruta")["Seed"]
        .apply(lambda x: ",".join(map(str, sorted(set(x)))))
        .to_dict()
    )

    df = df.drop_duplicates(subset=["Ruta"]).copy()
    df["SeedsEncontrada"] = df["Ruta"].map(semillas_ruta)

    columnas_obj = ["Latencia", "Perdida", "Jitter", "AnchoBanda"]
    claves = df[columnas_obj].round(12).astype(str).agg("|".join, axis=1)
    df = df.loc[~claves.duplicated()].copy()

    return df.reset_index(drop=True), total_inicial


def construir_frente(df):
    """Conserva únicamente las soluciones no dominadas globalmente."""

    no_dominadas = []

    for i in range(len(df)):
        solucion = df.iloc[i]

        dominada = any(
            j != i and domina(df.iloc[j], solucion)
            for j in range(len(df))
        )

        if not dominada:
            no_dominadas.append(i)

    frente = df.iloc[no_dominadas].copy()
    frente = frente.sort_values(
        ["Latencia", "Perdida", "Jitter", "AnchoBanda"],
        ascending=[True, True, True, False]
    ).reset_index(drop=True)

    frente.insert(0, "SolucionReferencia", range(1, len(frente) + 1))
    return frente


def main():
    print("=" * 70)
    print("CONSTRUCCIÓN DEL FRENTE PARETO DE REFERENCIA EMPÍRICO")
    print("=" * 70)

    combinadas = cargar_soluciones()
    unicas, total_inicial = eliminar_duplicados(combinadas)
    referencia = construir_frente(unicas)

    combinadas.to_csv(ARCHIVO_TODAS, index=False)
    referencia.to_csv(ARCHIVO_REFERENCIA, index=False)

    resumen = pd.DataFrame([{
        "SolucionesTotales30Seeds": total_inicial,
        "SolucionesUnicas": len(unicas),
        "SolucionesFrenteReferencia": len(referencia),
        "SolucionesDominadasEliminadas": len(unicas) - len(referencia)
    }])

    resumen.to_csv(ARCHIVO_RESUMEN, index=False)

    print(f"Soluciones combinadas:        {total_inicial}")
    print(f"Soluciones únicas:            {len(unicas)}")
    print(f"Frente de referencia:         {len(referencia)}")
    print(f"Dominadas eliminadas:         {len(unicas) - len(referencia)}")
    print(f"\nResultado guardado en:\n{ARCHIVO_REFERENCIA}")


if __name__ == "__main__":
    main()
