from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
RESULTADOS = BASE_DIR/"Resultados"/"ComparacionOriginalMejorada"
COMPARACION = RESULTADOS/"ComparacionMetricas.csv"
RESUMEN = RESULTADOS/"ResumenVersiones.csv"
OUTPUT_DIR = RESULTADOS/"Visualizaciones"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def guardar(nombre):
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / nombre, dpi=300, bbox_inches="tight")
    plt.close()


def grafica_gaps(df):
    x = range(len(df))
    ancho = 0.35

    plt.figure(figsize=(9, 5))
    plt.bar([i - ancho/2 for i in x], df["GapOriginal"], ancho, label="Original")
    plt.bar([i + ancho/2 for i in x], df["GapMejorada"], ancho, label="Mejorada")

    plt.xticks(list(x), df["Metrica"])
    plt.ylabel("Gap respecto al óptimo (%)")
    plt.title("Calidad de soluciones: Original vs Mejorada")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)

    guardar("01_ComparacionGaps.png")


def grafica_pareto(df):
    plt.figure(figsize=(7, 5))
    barras = plt.bar(df["Version"], df["SolucionesParetoExternas"])

    plt.ylabel("Soluciones no dominadas")
    plt.title("Tamaño del frente Pareto")

    for barra, valor in zip(barras, df["SolucionesParetoExternas"]):
        plt.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height() + 0.5,
            f"{int(valor)}",
            ha="center"
        )

    guardar("02_ComparacionPareto.png")


def grafica_tiempo(df):
    plt.figure(figsize=(7, 5))
    barras = plt.bar(df["Version"], df["TiempoSegundos"])

    plt.ylabel("Tiempo de ejecución (s)")
    plt.title("Tiempo de ejecución")

    for barra, valor in zip(barras, df["TiempoSegundos"]):
        plt.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height() + 1,
            f"{valor:.1f} s",
            ha="center"
        )

    guardar("03_ComparacionTiempo.png")


def main():
    if not COMPARACION.exists() or not RESUMEN.exists():
        raise FileNotFoundError(
            "Primero ejecuta 10_CompararOriginalMejorada.py."
        )

    comparacion = pd.read_csv(COMPARACION)
    resumen = pd.read_csv(RESUMEN)

    grafica_gaps(comparacion)
    grafica_pareto(resumen)
    grafica_tiempo(resumen)

if __name__ == "__main__":
    main()