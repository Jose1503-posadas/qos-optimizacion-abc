# Generación de Datos de la Red

Para evaluar el algoritmo de optimización de QoS, se genera una red sintética que simula condiciones realistas de telecomunicaciones. Esta red se modela como un grafo dirigido donde cada enlace contiene métricas clave de calidad de servicio.

## Modelo de Red

La topología de la red se construye utilizando el modelo de Barabási-Albert implementado mediante la librería NetworkX. Este modelo permite generar redes de libre escala, similares a infraestructuras reales como Internet, donde algunos nodos funcionan como hubs altamente conectados.

En el código, la red se crea con:

```python
G = nx.barabasi_albert_graph(n, m)
G = G.to_directed()
```

Donde:

- `n` representa el número total de nodos de la red.
- `m` indica el número de conexiones nuevas que crea cada nodo al incorporarse a la red.

Posteriormente, el grafo se convierte en dirigido para representar enlaces con flujo de tráfico en un único sentido.

---

## Asignación de Métricas QoS

Una vez generada la topología, se asignan métricas de Calidad de Servicio (QoS) a cada enlace del grafo utilizando valores aleatorios controlados.

Esto se realiza recorriendo cada arista:

```python
for u, v in G.edges():
```

Cada enlace `(u,v)` recibe las siguientes métricas:

### 1. Ancho de Banda (Bandwidth)

El ancho de banda representa la capacidad de transmisión del enlace y se genera aleatoriamente en un rango de 10 a 200 Mbps:

```python
bw = random.uniform(10, 200)
```

Esto permite simular enlaces con diferentes capacidades de transmisión.

---

### 2. Latencia

La latencia representa el tiempo de retardo de transmisión y se calcula utilizando una latencia base aleatoria más un factor asociado al ancho de banda:

```python
base_latencia = random.uniform(1, 100)
latencia = base_latencia + (1 / bw) * 100
```

De esta forma, enlaces con menor ancho de banda generan una penalización adicional de latencia, simulando posibles efectos de congestión.

---

### 3. Jitter

El jitter representa la variación del retardo en la transmisión de paquetes. En la implementación, esta métrica depende parcialmente de la latencia:

```python
jitter = random.uniform(0, 5) + 0.1 * latencia
```

Esto modela el comportamiento típico de redes reales, donde mayores retardos suelen producir una mayor variabilidad temporal.

---

### 4. Pérdida de Paquetes

La pérdida de paquetes se genera utilizando valores pequeños típicos en redes de comunicación:

```python
loss = random.uniform(0.0001, 0.01) + (1 / bw) * 0.05
```

La fórmula incorpora una dependencia inversa con el ancho de banda, haciendo que enlaces con menor capacidad presenten una probabilidad ligeramente mayor de pérdida.

---

## Almacenamiento de Datos

Finalmente, todas las métricas generadas se almacenan como atributos de cada enlace dentro del grafo:

```python
G[u][v]['AnchoBanda'] = bw
G[u][v]['latencia'] = latencia
G[u][v]['jitter'] = jitter
G[u][v]['PaquetesPerdidos'] = loss
```
---

# Normalización de las Métricas QoS

Después de generar y almacenar las métricas de QoS de la red, se realiza un proceso de normalización de datos. Esta etapa es fundamental para evitar que métricas con escalas mayores dominen el proceso de optimización.

Para ello, se utiliza la librería Pandas para cargar el dataset generado. Posteriormente, se crea una copia del conjunto de datos original para conservar los valores iniciales:

```python
df_norm = df.copy()
```

Las columnas seleccionadas para normalización corresponden a las métricas QoS:

```python
columnas = ["AnchoBanda", "Latencia", "jitter", "PaquetesPerdidos"]
```

---

## Método de Normalización

Se aplica una normalización Min-Max a cada métrica, transformando los valores al rango `[0,1]`.

La fórmula utilizada es:

```text
(valor - mínimo) / (máximo - mínimo)
```

En el código, este proceso se implementa mediante:

```python
for col in columnas:
    min_val = df[col].min()
    max_val = df[col].max()

    if max_val - min_val != 0:
        df_norm[col] = (df[col] - min_val) / (max_val - min_val)
    else:
        df_norm[col] = 0
```

Esta validación evita divisiones entre cero en caso de que todos los valores de una columna sean iguales.

---

## Inversión del Ancho de Banda

Dentro del problema de optimización QoS, algunas métricas deben minimizarse, como:

- Latencia
- Jitter
- Pérdida de paquetes

Sin embargo, el ancho de banda representa una métrica de maximización, ya que valores mayores son preferibles.

Para mantener un criterio uniforme de optimización, el ancho de banda se invierte utilizando:

```python
df_norm["AnchoBanda"] = 1 - df_norm["AnchoBanda"]
```

Con esta transformación:

- Valores altos de ancho de banda producen costos menores
- Valores bajos producen costos mayores

Esto permite tratar todas las métricas bajo una misma lógica de minimización.

---

## Almacenamiento del Dataset Normalizado

Una vez completada la normalización, el nuevo conjunto de datos se almacena en un archivo CSV:

```python
df_norm.to_csv("DatasetRed_Normalizado.csv", index=False)
```

El archivo resultante contiene todas las métricas escaladas y preparadas para ser utilizadas en algoritmos de optimización y selección de rutas QoS.

---

## Verificación Estadística

Finalmente, se imprimen estadísticas descriptivas del dataset normalizado:

```python
print(df_norm.describe())
```

Esto permite verificar:

- valores mínimos y máximos
- medias
- desviaciones estándar
- distribución general de las métricas normalizadas

asegurando que los datos estén correctamente preparados para el análisis posterior.