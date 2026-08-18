import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("../Red_datasets/ParetoResultados.csv")

plt.figure(figsize=(10,5))

plt.plot( df["Iteracion"], df["MejorFitness"],linewidth=2)

plt.xlabel("Iteraciones")
plt.ylabel("Mejor Fitness Global")
plt.title("Convergencia del ABC Multiobjetivo")
plt.grid(True)

plt.show()
