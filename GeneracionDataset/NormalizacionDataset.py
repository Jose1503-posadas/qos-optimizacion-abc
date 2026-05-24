import pandas as pd

# Leer dataset original
df = pd.read_csv("../Red_datasets/DatasetRed.csv")

df_norm = df.copy()

columnas = ["AnchoBanda", "Latencia", "jitter","PaquetesPerdidos"]

for col in columnas:
    min_val = df[col].min()
    max_val = df[col].max()
    # evitar división entre cero
    if max_val - min_val != 0:
        df_norm[col] = ((df[col] - min_val) /(max_val - min_val))
    else:
        df_norm[col] = 0

# invertir ancho de banda (maximización -> minimización)
df_norm["AnchoBanda"] = 1- df_norm["AnchoBanda"]

# Guardar dataset normalizado
df_norm.to_csv("../Red_datasets/DatasetRed_Normalizado.csv",index=False)

print(df_norm.describe())
