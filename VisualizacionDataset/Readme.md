# Visualización de la topología de red

En esta Sección permite cargar la red previamente normalizada desde un archivo CSV y generar una representación gráfica de su topología, facilitando la inspección visual de los nodos y enlaces antes de ejecutar el algoritmo ABC.

---

## 1. Carga del dataset normalizado

Se carga el archivo `DatasetRed_Normalizado.csv`, el cual contiene la información de los enlaces de la red junto con sus métricas QoS previamente normalizadas.

```python
df = pd.read_csv("DatasetRed_Normalizado.csv")
```

### Ejemplo de estructura del dataset

| Origen | Destino | AnchoBanda | Latencia | Jitter | PaquetesPerdidos |
|--------|---------|------------|----------|--------|------------------|
| 0 | 5 | 0.34 | 0.62 | 0.41 | 0.08 |
| 0 | 8 | 0.27 | 0.45 | 0.33 | 0.11 |

Cada fila representa una conexión dirigida entre dos nodos.

---

## 2. Construcción del grafo

A partir del DataFrame se construye un grafo dirigido:

```python
G = nx.from_pandas_edgelist(
    df,
    source="Origen",
    target="Destino",
    create_using=nx.DiGraph()
)
```

### Parámetros utilizados

- `source="Origen"`: columna que representa el nodo de salida.
- `target="Destino"`: columna que representa el nodo de llegada.
- `nx.DiGraph()`: crea un grafo dirigido.

Cada fila del CSV se transforma automáticamente en una arista del grafo.

### Ejemplo

Como el dataset contiene:

| Origen | Destino |
|--------|---------|
| 0 | 5 |
| 5 | 12 |

El grafo tendrá la estructura:

```text
0 → 5 → 12
```

## 3. Cálculo de posiciones de los nodos

Se calcula automáticamente la posición de cada nodo:

```python
pos = nx.spring_layout(
    G,
    seed=42
)
```

La función `spring_layout()` utiliza un modelo basado en fuerzas:

- los nodos se repelen entre sí,
- las conexiones actúan como resortes.


## 4. Impresión visual del grafo

La representación gráfica de la red se realiza mediante:

```python
nx.draw(
    G,
    pos,
    with_labels=True,
    node_size=500,
    arrows=True
)
```

### Parámetros utilizados

#### `G`

Contiene toda la estructura del grafo:

- nodos
- enlaces
- direcciones

#### `pos`

Define las coordenadas donde será dibujado cada nodo.

#### `with_labels=True`

Muestra el identificador de cada nodo.

Ejemplo:

```text
0   1   2   3
```

#### `node_size=500`

Define el tamaño visual de cada nodo.

#### `arrows=True`

Muestra flechas para representar la dirección de los enlaces.

Ejemplo:

```text
0 → 5 → 12
```

## Resultado

La visualización final permite observar:

- **Cada nodo** como un vértice de la red.
- **Cada flecha** como un enlace dirigido.
- **La conectividad global** entre nodos.
- **La estructura topológica** antes de ejecutar el algoritmo de optimización.

Esto permite validar visualmente que la red fue construida correctamente a partir del dataset normalizado antes de aplicar el algoritmo de Colonia de Abejas Artificiales (ABC).