from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
RESULTADOS = BASE_DIR / "Resultados" / "Mejorada" / "03_MultiplesSemillas"
ARCHIVO = RESULTADOS / "ResumenCorridas.csv"
OUTPUT_DIR = RESULTADOS / "Visualizaciones"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def guardar(nombre):
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / nombre, dpi=300, bbox_inches="tight")
    plt.close()

def grafica_exito(df):
    tasas = [
        df["OptimoLatencia"].mean() * 100,
        df["OptimoPerdida"].mean() * 100,
        df["OptimoJitter"].mean() * 100,
        df["OptimoAnchoBanda"].mean() * 100
    ]

    plt.figure(figsize=(8, 5))
    plt.bar(["Latencia", "Pérdida", "Jitter", "Ancho de banda"], tasas)
    plt.ylabel("Tasa de éxito (%)")
    plt.title("Éxito por objetivo en 30 semillas")
    plt.ylim(0, 105)

    for i, valor in enumerate(tasas):
        plt.text(i, valor + 1, f"{valor:.2f}%", ha="center")

    guardar("01_ExitoPorObjetivo.png")

def grafica_pareto(df):
    plt.figure(figsize=(9, 5))
    plt.plot(df["Seed"], df["TamanoPareto"], marker="o")
    plt.axhline(df["TamanoPareto"].mean(), linestyle="--", label=f"Media = {df['TamanoPareto'].mean():.2f}")
    plt.xlabel("Seed")
    plt.ylabel("Soluciones Pareto")
    plt.title("Tamaño del frente Pareto por seed")
    plt.xticks(df["Seed"])
    plt.grid(alpha=0.3)
    plt.legend()
    guardar("02_ParetoPorSeed.png")


def grafica_gap_bw(df):
    plt.figure(figsize=(9, 5))
    plt.bar(df["Seed"], df["GapAnchoBanda"])
    plt.xlabel("Seed")
    plt.ylabel("Gap de ancho de banda (%)")
    plt.title("Gap respecto al óptimo de ancho de banda")
    plt.xticks(df["Seed"])
    plt.grid(axis="y", alpha=0.3)
    guardar("03_GapAnchoBanda.png")


def main():
    if not ARCHIVO.exists():
        raise FileNotFoundError(
            f"No se encontró:\n{ARCHIVO}\n"
            "Ejecuta primero 06_ExperimentoMultiplesSemillas.py."
        )

    df = pd.read_csv(ARCHIVO).sort_values("Seed")

    grafica_exito(df)
    grafica_pareto(df)
    grafica_gap_bw(df)

if __name__ == "__main__":
    main()