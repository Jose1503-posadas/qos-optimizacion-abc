# Datasets de la Red QoS



<p>
Esta carpeta contiene los datasets utilizados durante el desarrollo,
evaluación y mejora del algoritmo de optimización multiobjetivo basado en
<strong>Artificial Bee Colony (ABC)</strong>.
</p>

---

## Estructura de la carpeta

```text
Red_datasets/
│
├── Original/
│   ├── DatasetRed.csv
│   └── DatasetRed_Normalizado.csv
│
├── Mejorada/
│   └── DatasetRed.csv
│
└── Readme.md
```
---

##  Versión Original

La carpeta `Original/` conserva los datasets utilizados por la primera versión del sistema de optimización.

###  `Original/DatasetRed.csv`

Contiene los datos generados a partir de una red construida mediante el modelo de **Barabási-Albert**.

Cada registro representa un enlace de la red.

Las métricas almacenadas son:

| Campo              | Descripción                           |
| ------------------ | ------------------------------------- |
| `Origen`           | Nodo donde inicia el enlace           |
| `Destino`          | Nodo donde termina el enlace          |
| `AnchoBanda`       | Capacidad disponible del enlace       |
| `Latencia`         | Tiempo de transmisión                 |
| `Jitter`           | Variación en el tiempo de transmisión |
| `PaquetesPerdidos` | Porcentaje de pérdida de paquetes     |

Las métricas se encuentran expresadas en sus **unidades y escalas originales**.

---

### `Original/DatasetRed_Normalizado.csv`

Este archivo corresponde al mismo conjunto de enlaces después de aplicar una transformación **Min-Max** a las métricas QoS.

La normalización utilizada fue:

```text
             x - xmin
x' = ─────────────────────
          xmax - xmin
```

De esta forma, los valores fueron transformados al intervalo: [0. 1]



En esta versión también se realizaba una transformación sobre el **ancho de banda**, debido a que esta métrica debe maximizarse, mientras que:

* Latencia
* Jitter
* Pérdida de paquetes

deben minimizarse.

Por esta razón, el ancho de banda era transformado para expresar todos los objetivos bajo un mismo criterio de minimización.

---

## Versión Mejorada

La carpeta `Mejorada/` contiene el dataset empleado por la versión revisada del algoritmo.

### `Mejorada/DatasetRed.csv`

En esta versión se utilizan directamente las métricas QoS en sus **valores reales**.

Por lo tanto, se conservan las unidades originales de:

| Métrica             | Unidad |
| ------------------- | ------ |
| Ancho de banda      | Mbps   |
| Latencia            | ms     |
| Jitter              | ms     |
| Pérdida de paquetes | %      |

El cambio permite que las métricas completas de una ruta sean calculadas **antes de realizar transformaciones adicionales para su comparación**.

---

## ¿Por qué se eliminó la normalización previa?

En la implementación original, cada enlace era normalizado individualmente antes de calcular las métricas completas de una ruta.

Para una métrica cualquiera:

```text
             x - xmin
x' = ─────────────────────
          xmax - xmin
```

Si una ruta contiene `k` enlaces, la suma de los valores normalizados es:

```text
Σ x'
```

lo cual puede expresarse como:

```text
          Σ(x - xmin)
Σx' = ─────────────────
          xmax - xmin
```

y, por tanto:

```text
           Σx - k · xmin
Σx' = ─────────────────────
             xmax - xmin
```

Esto introduce el término:

```text
k · xmin
```

que depende directamente del **número de enlaces de la ruta**.

Como consecuencia, la transformación no funciona únicamente como un cambio de escala cuando se aplica **antes de agregar las métricas de los enlaces**.

También puede modificar indirectamente la forma en que se comparan rutas con diferente cantidad de saltos.

