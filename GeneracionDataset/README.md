<div align="left">

# Generación de Datos de la Red

<br>

Este módulo genera una red considerando simultáneamente métricas de Calidad de Servicio como **latencia, jitter, pérdida de paquetes y ancho de banda**.

</div>

---

# Descripción

Para evaluar el comportamiento del algoritmo de optimización se requiere una topología de red que permita generar y analizar diferentes rutas entre un nodo origen y un nodo destino.

En este proyecto se utiliza una **red**, que permite controlar las condiciones experimentales y repetir los experimentos bajo configuraciones conocidas.

Entre las ventajas de este enfoque se encuentran:

* generación controlada de la red
* ejecución de múltiples escenarios
* reproducción de experimentos mediante semillas
* comparación entre versiones del algoritmo
* análisis individual de las métricas de QoS
* generación de diferentes instancias de red sin depender de infraestructura física

Cada enlace dirigido contiene cuatro métricas principales:

<table>
<tr>
<th>Métrica</th>
<th>Representación</th>
<th>Objetivo</th>
</tr>

<tr>
<td><b>Ancho de banda disponible</b></td>
<td>Mbps</td>
<td>⬆ Maximizar</td>
</tr>

<tr>
<td><b>Latencia</b></td>
<td>Milisegundos (ms)</td>
<td>⬇ Minimizar</td>
</tr>

<tr>
<td><b>Jitter</b></td>
<td>Milisegundos (ms)</td>
<td>⬇ Minimizar</td>
</tr>

<tr>
<td><b>Pérdida de paquetes</b></td>
<td>Proporción entre 0 y 1</td>
<td>⬇ Minimizar</td>
</tr>
</table>



---

# Modelo de Red

La topología se genera utilizando el modelo **Barabási-Albert**, implementado mediante la librería `NetworkX`.

El modelo genera redes mediante un mecanismo conocido como **preferential attachment**, donde los nuevos nodos tienen mayor probabilidad de conectarse con nodos que ya poseen un mayor número de conexiones.

La creación de la red se realiza mediante:

```python
base = nx.barabasi_albert_graph(
    n=n,
    m=m,
    seed=seed
)
```

Donde:

* `n` representa el número total de nodos
* `m` representa el número de enlaces que crea cada nuevo nodo
* `seed` permite reproducir la misma red

Antes de generar la red se valida que:

```text
1 <= m < n
```

mediante:

```python
if not 1 <= m < n:
    raise ValueError("Debe cumplirse 1 <= m < n")
```

Posteriormente, la red no dirigida generada por Barabási-Albert se convierte en una red dirigida:

```python
G = base.to_directed()
```

Esto permite tratar independientemente los enlaces:

`u → v` &nbsp;&nbsp;&nbsp; y &nbsp;&nbsp;&nbsp; `v → u`

De esta manera, cada dirección puede almacenar sus propias métricas QoS.

---

# Evolución del Generador de la Red

Durante el desarrollo del proyecto se utilizaron dos versiones principales del generador de red.

La primera versión permitió construir el entorno experimental inicial y verificar el funcionamiento general del algoritmo.

Después del análisis de dicha implementación se identificaron oportunidades de mejora relacionadas principalmente con:

* reproducibilidad
* representación de la congestión
* relación entre las métricas QoS
* interpretación física de los datos
* organización del dataset
* proceso de normalización

<div align="center">
</div>

---

### Comparación

<table>
<tr>
<th width="25%">Característica</th>
<th width="37%"> Versión Original</th>
<th width="38%"> Versión Mejorada</th>
</tr>

<tr>
<td><b>Modelo</b></td>
<td>Barabási-Albert</td>
<td>Barabási-Albert</td>
</tr>

<tr>
<td><b>Topología dirigida</b></td>
<td> Sí</td>
<td> Sí</td>
</tr>

<tr>
<td><b>Semilla reproducible</b></td>
<td> No</td>
<td> Sí</td>
</tr>

<tr>
<td><b>Random de Python</b></td>
<td>Sin controlar</td>
<td><code>random.Random(seed)</code></td>
</tr>

<tr>
<td><b>NumPy</b></td>
<td>No utilizado para congestión</td>
<td><code>np.random.default_rng(seed)</code></td>
</tr>

<tr>
<td><b>Topología NetworkX</b></td>
<td>Sin semilla</td>
<td>Semilla controlada</td>
</tr>

<tr>
<td><b>Capacidad</b></td>
<td>10–200 Mbps</td>
<td>50–1000 Mbps</td>
</tr>

<tr>
<td><b>Utilización explícita</b></td>
<td> No</td>
<td> Distribución Beta</td>
</tr>

<tr>
<td><b>Ancho de banda</b></td>
<td>Capacidad generada directamente</td>
<td>Ancho de banda disponible según utilización</td>
</tr>

<tr>
<td><b>Congestión</b></td>
<td>Representación indirecta mediante <code>1 / bw</code></td>
<td>Representación explícita mediante utilización</td>
</tr>

<tr>
<td><b>Latencia</b></td>
<td>Latencia base + penalización por ancho de banda</td>
<td>Propagación + retardo por cola + variación</td>
</tr>

<tr>
<td><b>Jitter</b></td>
<td>Dependiente directamente de latencia</td>
<td>Relacionado principalmente con congestión</td>
</tr>

<tr>
<td><b>Pérdida</b></td>
<td>Dependiente de <code>1 / bw</code></td>
<td>Aumenta no linealmente con utilización</td>
</tr>

<tr>
<td><b>Normalización externa</b></td>
<td> Min-Max</td>
<td> Eliminada</td>
</tr>
</table>

---

# Versión Original

<details>

<summary><b> Mostrar funcionamiento de la versión original</b></summary>

<br>

La implementación inicial generaba la red mediante:

```python
G = nx.barabasi_albert_graph(n, m)
G = G.to_directed()
```

Posteriormente se asignaban las métricas QoS.

## Ancho de Banda

```python
bw = random.uniform(10, 200)
```

El ancho de banda se generaba directamente en un intervalo de:

```text
10 – 200 Mbps
```

---

## Latencia

```python
base_latencia = random.uniform(1, 100)

latencia = (
    base_latencia
    + (1 / bw) * 100
)
```

El término:

```python
(1 / bw) * 100
```

introducía una penalización mayor para enlaces con menor ancho de banda.

---

## Jitter

```python
jitter = (
    random.uniform(0, 5)
    + 0.1 * latencia
)
```

El jitter dependía directamente del valor completo de la latencia.

---

## Pérdida de Paquetes

```python
loss = (
    random.uniform(0.0001, 0.01)
    + (1 / bw) * 0.05
)
```

La pérdida aumentaba automáticamente en enlaces con menor ancho de banda.

</details>

---

# Limitaciones de la Versión Original

La primera implementación fue útil para construir el entorno experimental inicial, pero durante el desarrollo se identificaron diferentes aspectos que podían mejorarse.

## 1. Falta de reproducibilidad

No existía una semilla definida para:

```python
random
```

ni para:

```python
nx.barabasi_albert_graph()
```

Por lo tanto, ejecutar dos veces:

```python
G = generarRed(n=100, m=4)
```

podía producir tanto una topología diferente como valores QoS diferentes.

Esto dificulta realizar comparaciones experimentales controladas.

---

## 2. La congestión no estaba representada explícitamente

En la versión original, la congestión se aproximaba mediante relaciones como:

```python
1 / bw
```

Sin embargo, la capacidad de un enlace y su nivel de utilización representan conceptos distintos.

Un enlace puede disponer de una capacidad elevada y encontrarse congestionado.

De manera similar, un enlace con menor capacidad puede encontrarse poco utilizado.

Por esta razón, en la nueva versión se decidió introducir explícitamente una variable de:

```text
utilización
```

---

## 3. Dependencia elevada entre jitter y latencia

La expresión:

```python
jitter = random.uniform(0, 5) + 0.1 * latencia
```

hacía que una parte importante del jitter estuviera determinada directamente por la latencia.

Aunque ambas métricas pueden estar relacionadas, representan propiedades diferentes de una comunicación.

Por este motivo, la nueva versión mantiene una relación indirecta mediante las condiciones de congestión.

---

## 4. Pérdida asociada directamente al ancho de banda

La expresión:

```python
(1 / bw) * 0.05
```

hacía que los enlaces de menor capacidad recibieran automáticamente una penalización adicional.

La nueva implementación relaciona la pérdida principalmente con el nivel de utilización.

---

# Versión Mejorada

La versión actual introduce un modelo donde las diferentes métricas QoS tienen como factor común las condiciones de utilización del enlace, pero conservan variación independiente.

---

# Reproducibilidad

Una de las mejoras principales consiste en controlar las fuentes de aleatoriedad.

## Random de Python

```python
rng = random.Random(seed)
```

## NumPy

```python
np_rng = np.random.default_rng(seed)
```

## NetworkX

```python
base = nx.barabasi_albert_graph(
    n=n,
    m=m,
    seed=seed
)
```

Por defecto se utiliza:

```python
seed=42
```

De esta manera, si se ejecuta nuevamente:

```python
generar_red(
    n=100,
    m=4,
    seed=42
)
```

se obtiene la misma instancia de red.
---

# Capacidad del Enlace

La nueva versión distingue entre:

* **capacidad física del enlace**;
* **capacidad actualmente utilizada**;
* **ancho de banda disponible**.

Primero se genera la capacidad:

```python
capacidad = rng.uniform(
    50.0,
    1000.0
)
```

El intervalo utilizado es:

```text
50 – 1000 Mbps
```

Esta variable representa la capacidad máxima del enlace antes de considerar su utilización.

---

# Utilización del Enlace

La utilización se genera mediante una distribución Beta:

```python
utilizacion = float(
    np_rng.beta(2.0, 4.0)
)
```

La distribución Beta permite obtener valores dentro del intervalo:

```text
0 ≤ utilización ≤ 1
```

donde:

```text
0.00 → enlace prácticamente libre
0.50 → aproximadamente 50 % utilizado
0.90 → enlace altamente utilizado
```

La elección de `Beta(2,4)` permite generar con mayor frecuencia situaciones de utilización baja o moderada, manteniendo la posibilidad de obtener enlaces con congestión elevada.

---

# Ancho de Banda Disponible

A diferencia de la versión original, la variable `AnchoBanda` ya no representa directamente la capacidad total del enlace.

Ahora representa la cantidad de capacidad que permanece disponible después de considerar la utilización.

```python
ancho_disponible = max(
    1.0,
    capacidad * (1.0 - utilizacion)
)
```

Por ejemplo:

```text
Capacidad física = 800 Mbps
Utilización      = 25 %

Ancho disponible:

800 × (1 - 0.25)

= 600 Mbps
```

Esta representación permite diferenciar entre la capacidad máxima del enlace y los recursos realmente disponibles.

---

# Retardo de Propagación

Se genera un retardo base:

```python
propagacion = rng.uniform(
    1.0,
    45.0
)
```

representado en milisegundos.

Este componente representa el retardo base del enlace antes de considerar efectos asociados con congestión.

---

# Retardo por Cola

La congestión se incorpora mediante:

```python
cola = (
    2.5 * utilizacion
    / max(
        1.0 - utilizacion,
        0.05
    )
)
```

Cuando la utilización es baja, el valor permanece pequeño.

A medida que la utilización aumenta, el término:

```text
utilización
────────────
1-utilización
```

crece de manera no lineal.

Conceptualmente:

| Nivel de utilización | Efecto sobre el retardo |
|---|---|
| **Baja** | Retardo de cola pequeño |
| **Media** | Retardo creciente |
| **Elevada** | Incremento considerable del retardo |

El límite:

```python
max(
    1.0 - utilizacion,
    0.05
)
```

evita que el denominador tome valores demasiado pequeños.

---

# Latencia

La latencia se obtiene combinando tres componentes:

```python
latencia = (
    propagacion
    + cola
    + rng.uniform(0.0, 2.0)
)
```

De forma conceptual:

```text
                LATENCIA
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
   Propagación    Cola    Variación
                              aleatoria
```

Esto permite que la latencia responda a las condiciones de congestión sin eliminar completamente la variabilidad entre enlaces.

---

#  Jitter

El jitter representa la variación temporal del retardo.

Se genera mediante:

```python
jitter = (
    rng.uniform(0.1, 3.0)
    + rng.uniform(0.05, 0.25) * cola
)
```

A diferencia de la versión anterior, ya no se calcula directamente como una fracción de toda la latencia.

Ahora mantiene:

* un componente independiente;
* un componente relacionado con congestión.

Esto permite conservar una correlación razonable entre congestión y jitter sin hacer que jitter y latencia sean prácticamente la misma variable escalada.

---

# Pérdida de Paquetes

Primero se genera una pérdida base:

```python
perdida_base = rng.uniform(
    0.00001,
    0.002
)
```

Posteriormente se incorpora el efecto de utilización:

```python
perdida = (
    perdida_base
    + 0.03 * (utilizacion ** 4)
)
```

El término:

```python
utilizacion ** 4
```

hace que el incremento sea pequeño bajo condiciones normales, pero aumente significativamente cuando el enlace se encuentra altamente utilizado.

Finalmente se establece un límite:

```python
perdida = min(
    max(perdida, 0.0),
    0.05
)
```

Por lo tanto:

```text
0.05 = 5 %
```

es la pérdida máxima permitida por el generador.

---

# Asignación de Métricas QoS

Cada enlace dirigido almacena sus propios atributos:

```python
G[u][v]["AnchoBanda"] = ancho_disponible

G[u][v]["Latencia"] = latencia

G[u][v]["jitter"] = jitter

G[u][v]["PaquetesPerdidos"] = perdida
```

El resultado conceptual es:

```text
Nodo u
  │
  │
  │   AnchoBanda
  │   Latencia
  │   Jitter
  │   PaquetesPerdidos
  │
  ▼
Nodo v
```

---

# Cambio en la Normalización

Una modificación importante respecto a la primera versión del proyecto es la eliminación del proceso independiente de normalización del dataset.
---

# Normalización Utilizada Anteriormente

<details>

<summary><b> Mostrar implementación anterior de normalización</b></summary>

<br>

El dataset original se cargaba mediante:

```python
df = pd.read_csv(
    "../Red_datasets/DatasetRed.csv"
)
```

Posteriormente se seleccionaban las métricas:

```python
columnas = [
    "AnchoBanda",
    "Latencia",
    "jitter",
    "PaquetesPerdidos"
]
```

Se utilizaba normalización Min-Max:

```python
for col in columnas:

    min_val = df[col].min()
    max_val = df[col].max()

    if max_val - min_val != 0:

        df_norm[col] = (
            (df[col] - min_val)
            / (max_val - min_val)
        )

    else:
        df_norm[col] = 0
```

La transformación utilizada era:

```text
                 x - xmin
x' = ─────────────────────────
             xmax - xmin
```

Esto llevaba los valores al intervalo:

```text
[0,1]
```

Posteriormente se invertía el ancho de banda:

```python
df_norm["AnchoBanda"] = (
    1 - df_norm["AnchoBanda"]
)
```

El objetivo era transformar todas las métricas hacia una lógica de minimización.

Finalmente se generaba:

```text
DatasetRed_Normalizado.csv
```

</details>

---

# ¿Por qué se dejó de normalizar?

> La decisión consiste específicamente en **no modificar permanentemente el dataset de entrada**, ya que la formulación actual conserva los objetivos de QoS de manera independiente.

---

## 1. La optimización es multiobjetivo

El problema considera los siguientes objetivos:

```text
Minimizar Latencia
Minimizar Jitter
Minimizar Pérdida de paquetes
Maximizar Ancho de banda
```

En un problema multiobjetivo basado en **dominancia de Pareto**, no es necesario sumar estas magnitudes para determinar si una solución domina a otra.

Por ejemplo, considerando dos soluciones:

```text
A = [latenciaA, jitterA, pérdidaA, anchoA]

B = [latenciaB, jitterB, pérdidaB, anchoB]
```

cada objetivo puede compararse de acuerdo con su propia dirección.

Por esta razón, todos los valores no necesitan estar dentro del mismo intervalo únicamente para aplicar dominancia.

---

## 2. Se conservan las unidades físicas

Sin normalización es posible obtener resultados como:

```text
Latencia       = 32.59 ms
Jitter         = 2.79 ms
Pérdida        = 0.00189
Ancho de banda = 508.44 Mbps
```

Estos resultados pueden interpretarse directamente.

Después de una transformación Min-Max podrían convertirse, por ejemplo, en:

```text
Latencia       = 0.31
Jitter         = 0.17
Pérdida        = 0.08
Ancho de banda = 0.46
```

Aunque estos números son válidos para determinados cálculos matemáticos, ya no permiten conocer directamente el comportamiento físico de la ruta.

Mantener las unidades originales facilita:

* interpretación de resultados
* comparación de rutas
* generación de tablas
* elaboración de gráficas
* análisis estadístico
* explicación de resultados en el reporte final

---


## 3. Min-Max depende del mínimo y máximo de cada dataset

La normalización Min-Max utiliza los valores **xmin** y **xmax** observados en cada conjunto de datos. Por ello, al generar nuevas instancias con diferentes semillas, estos extremos pueden cambiar.

| Red | Latencia mínima | Latencia máxima |
|:---:|:---:|:---:|
| **A** | 2 ms | 60 ms |
| **B** | 4 ms | 100 ms |

Por ejemplo, un valor normalizado de **0.50** no representa necesariamente la misma cantidad de milisegundos en ambas redes.

Por esta razón conservar las unidades originales facilita la comparación de resultados entre diferentes instancias.

---

## 4. La normalización anterior se aplicaba por enlace

Existe otra consideración importante.

Anteriormente se normalizaba cada enlace antes de calcular las métricas completas de una ruta.

Para una métrica cualquiera:

```text
                 x - xmin
x' = ─────────────────────────
             xmax - xmin
```

Si una ruta contiene `k` enlaces y posteriormente se suman sus valores:

```text
Σ x'
```

entonces:

```text
          Σ(x - xmin)
Σx' = ─────────────────
          xmax - xmin
```

que equivale a:

```text
           Σx - k · xmin
Σx' = ─────────────────────
             xmax - xmin
```

Esto introduce un término:

```text
k · xmin
```

dependiente del número de enlaces de la ruta.

Por tanto, la transformación no funciona únicamente como cambio de escala cuando se normaliza **antes de agregar los enlaces**.

También puede modificar indirectamente la manera en que se penalizan rutas con diferente número de saltos.

Por esta razón, resulta preferible calcular primero las métricas reales de cada ruta.

---

# Referencias

## Modelo Barabási-Albert

**Barabási, A. L., & Albert, R. (1999).**
*Emergence of Scaling in Random Networks.*
Science, 286(5439), 509–512.

---

## NetworkX

**NetworkX Developers.**
*barabasi_albert_graph — NetworkX Documentation.*

```text
https://networkx.org/documentation/stable/reference/generated/networkx.generators.random_graphs.barabasi_albert_graph.html
```


## Optimización Multiobjetivo

**Emmerich, M. T. M., & Deutz, A. H. (2018).**
*A tutorial on multiobjective optimization: fundamentals and evolutionary methods.*
Natural Computing, 17, 585–609.

## Normalización Min-Max

**Scikit-learn Developers.**
*MinMaxScaler — scikit-learn Documentation.*

```text
https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html
```
---


