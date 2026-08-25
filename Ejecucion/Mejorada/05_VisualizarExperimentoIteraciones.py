from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

RESULTADOS = BASE_DIR/"Resultados"/"Mejorada"/"02_ExperimentoIteraciones"
ARCHIVO = RESULTADOS/"ResumenPorIteraciones.csv"
OUTPUT_DIR =RESULTADOS/"Visualizaciones"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def guardar_grafica(nombre):
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / nombre, dpi=300, bbox_inches="tight")
    plt.close()

def grafica_exito(df):
    plt.figure(figsize=(8, 5))
    plt.plot(df["Iteraciones"], df["ExitoCompleto"], marker="o", linewidth=2)
    plt.xlabel("Número de iteraciones")
    plt.ylabel("Ejecuciones con los 4 óptimos (%)")
    plt.title("Tasa de éxito completa vs. iteraciones")
    plt.xticks(df["Iteraciones"])
    plt.ylim(0, 105)
    plt.grid(alpha=0.3)
    guardar_grafica("01_ExitoCompleto.png")

def grafica_tiempo(df):
    plt.figure(figsize=(8, 5))
    plt.plot(df["Iteraciones"], df["TiempoPromedio"], marker="o", linewidth=2)
    plt.xlabel("Número de iteraciones")
    plt.ylabel("Tiempo promedio (s)")
    plt.title("Tiempo de ejecución vs. iteraciones")
    plt.xticks(df["Iteraciones"])
    plt.grid(alpha=0.3)
    guardar_grafica("02_TiempoPromedio.png")

def grafica_pareto(df):
    plt.figure(figsize=(8, 5))
    plt.plot(df["Iteraciones"], df["ParetoPromedio"], marker="o", linewidth=2)
    plt.xlabel("Número de iteraciones")
    plt.ylabel("Soluciones Pareto promedio")
    plt.title("Tamaño del frente Pareto vs. iteraciones")
    plt.xticks(df["Iteraciones"])
    plt.grid(alpha=0.3)
    guardar_grafica("03_ParetoPromedio.png")

def grafica_diversidad(df):
    plt.figure(figsize=(8, 5))
    plt.plot(df["Iteraciones"], df["DiversidadPromedio"], marker="o", linewidth=2)
    plt.xlabel("Número de iteraciones")
    plt.ylabel("Diversidad promedio")
    plt.title("Diversidad de rutas vs. iteraciones")
    plt.xticks(df["Iteraciones"])
    plt.grid(alpha=0.3)
    guardar_grafica("04_DiversidadPromedio.png")

def grafica_objetivos(df):
    plt.figure(figsize=(9, 5))
    plt.plot(df["Iteraciones"], df["ExitoLatencia"], marker="o", label="Latencia")
    plt.plot(df["Iteraciones"], df["ExitoPerdida"], marker="o", label="Pérdida")
    plt.plot(df["Iteraciones"], df["ExitoJitter"], marker="o", label="Jitter")
    plt.plot(df["Iteraciones"], df["ExitoAnchoBanda"], marker="o", label="Ancho de banda")
    plt.xlabel("Número de iteraciones")
    plt.ylabel("Tasa de éxito (%)")
    plt.title("Éxito por objetivo vs. iteraciones")
    plt.xticks(df["Iteraciones"])
    plt.ylim(0, 105)
    plt.grid(alpha=0.3)
    plt.legend()
    guardar_grafica("05_ExitoPorObjetivo.png")

def main():
    if not ARCHIVO.exists():
        raise FileNotFoundError(
            f"No se encontró:\n{ARCHIVO}\n"
            "Ejecuta primero 04_ExperimentoIteraciones.py."
        )

    df = pd.read_csv(ARCHIVO).sort_values("Iteraciones")

    grafica_exito(df)
    grafica_tiempo(df)
    grafica_pareto(df)
    grafica_diversidad(df)
    grafica_objetivos(df)

if __name__ == "__main__":
    main()