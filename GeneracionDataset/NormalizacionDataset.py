import pandas as pd

df = pd.read_csv("DatasetRed.csv")

df_norm = df.copy()

columnas = ["AnchoBanda", "Latencia", "jitter", "PaquetesPerdidos"]

for col in columnas:
    min_val = df[col].min()
    max_val = df[col].max()

    # evitar división entre cero (por si todos los valores fueran iguales)
    if max_val - min_val != 0:
        df_norm[col] = (df[col] - min_val) / (max_val - min_val)
    else:
        df_norm[col] = 0

# invertir ancho de banda (porque es maximización)
df_norm["AnchoBanda"] = 1 - df_norm["AnchoBanda"]

# Almacenar en CSV
df_norm.to_csv("DatasetRed_Normalizado.csv", index=False)

print(df_norm.describe())