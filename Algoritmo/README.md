# Optimización Multiobjetivo de QoS mediante Artificial Bee Colony

## Descripción

Este módulo contiene la versión mejorada del algoritmo **Artificial Bee Colony (ABC) Multiobjetivo** utilizado para encontrar rutas de comunicación eficientes dentro de una red de telecomunicaciones.

El problema se aborda como una optimización multiobjetivo, donde cada ruta debe considerar simultáneamente cuatro métricas de Calidad de Servicio (**QoS**):

| Métrica | Objetivo |
|---|---|
| Latencia | Minimizar |
| Pérdida de paquetes | Minimizar |
| Jitter | Minimizar |
| Ancho de banda | Maximizar |

Debido a que mejorar una métrica puede empeorar otra, el algoritmo no devuelve una única ruta, sino un **frente de Pareto formado por soluciones no dominadas**.

---

## Representación de la red

La red se representa mediante un grafo dirigido utilizando `NetworkX`.

Cada elemento tiene la siguiente interpretación:

| Elemento | Representación |
|---|---|
| Nodo | Dispositivo o punto de comunicación |
| Arista | Enlace dirigido entre dos dispositivos |
| Ruta | Solución candidata |
| Métricas QoS | Características asociadas a cada enlace |

Cada enlace contiene:
- Latencia
- PaquetesPerdidos
- jitter
- AnchoBanda


El algoritmo trabaja directamente con las métricas reales almacenadas en el dataset.

---

## Evaluación de una ruta

Una ruta se representa como:

```text
Origen → Nodo1 → Nodo2 → ... → Destino
```

Para cada ruta se calculan cuatro objetivos.

### Latencia

La latencia total corresponde a la suma de las latencias de todos los enlaces:

$$
L(R) = \sum_{e \in R} L_e
$$

---

### Pérdida de paquetes

La pérdida se calcula como una probabilidad extremo a extremo:

$$
P_{\text{loss}}(R) =
1 - \prod_{e \in R}(1-p_e)
$$

Esto permite representar la probabilidad real de que al menos un paquete
se pierda durante el recorrido completo.

---

### Jitter

El jitter de la ruta se obtiene acumulando el jitter de sus enlaces:

$$
J(R) = \sum_{e \in R} J_e
$$

---

### Ancho de banda

El ancho de banda disponible de una ruta está limitado por su enlace con menor capacidad.

Por ello se utiliza el **cuello de botella**:

$$
BW(R) = \min_{e \in R}(BW_e)
$$

---

## Vector de objetivos

Internamente todos los objetivos son tratados como problemas de minimización:

$$
Fitness(R) =
\left(
Latencia,\;
Pérdida,\;
Jitter,\;
-AnchoBanda
\right)
$$

El ancho de banda se almacena con signo negativo únicamente para mantener una misma regla de dominancia.

Por ejemplo:

```python
fitness = abc.evaluar(ruta)
```

Para mostrar los resultados con el ancho de banda nuevamente positivo se utiliza:

```python
metricas = abc.fitness_para_mostrar(fitness)
```

---

## Normalización de métricas

La versión mejorada utiliza normalización Min-Max para comparar las métricas durante la **construcción y modificación de rutas**.

\[
x'=\frac{x-x_{min}}{x_{max}-x_{min}}
\]

> **Importante:** la normalización no se utiliza para calcular el frente de Pareto.

Las soluciones finales siguen siendo evaluadas utilizando los valores reales del dataset.

Esto evita que una métrica domine la construcción de rutas únicamente por manejar valores numéricos de mayor escala.

---

# Algoritmo ABC Multiobjetivo

El algoritmo conserva los tres tipos principales de abejas del modelo Artificial Bee Colony:

## 🐝 Abejas obreras

Cada abeja obrera mantiene una ruta y genera una solución vecina.

La nueva solución puede reemplazar a la actual cuando:

- domina a la solución existente;
- aporta mayor diversidad al espacio objetivo;
- o es aceptada ocasionalmente como movimiento exploratorio.

Esto permite mantener un equilibrio entre **explotación y exploración**.

---

## 🐝 Abejas espectadoras

Las abejas espectadoras seleccionan soluciones de la población mediante una estrategia basada en:

- nivel de dominancia;
- frente no dominado al que pertenece la solución;
- distancia de crowding;
- exploración probabilística.

Las soluciones con mejor calidad tienen mayor probabilidad de ser seleccionadas, sin eliminar completamente la posibilidad de explorar otras regiones.

---

## 🐝 Abejas exploradoras

Cada solución mantiene un contador de intentos sin mejora.

Cuando una abeja supera un límite determinado:

```text
LIMITE
```

su ruta puede ser reemplazada por una nueva solución generada desde cero.

Esto permite abandonar regiones estancadas del espacio de búsqueda.

---

# Generación de rutas

La construcción de rutas combina búsqueda guiada por QoS y exploración aleatoria.

Para evitar generar soluciones inválidas se consideran varias restricciones:

```text
✓ La ruta inicia en el nodo origen
✓ La ruta termina en el nodo destino
✓ Todos los enlaces deben existir
✓ No se permiten ciclos
✓ No se permiten nodos repetidos
✓ Se respeta una longitud máxima
```

La selección de los siguientes nodos utiliza costos QoS normalizados y diferentes combinaciones aleatorias de pesos.

Esto permite generar rutas orientadas hacia diferentes compromisos entre los cuatro objetivos.

---

# Operadores de vecindario

La versión mejorada utiliza tres operadores especializados para modificar las rutas.

## 1. Desvío de sufijo

Conserva la primera parte de una ruta y genera un nuevo camino desde un nodo intermedio hasta el destino.

```text
Ruta original

A → B → C → D → E
        │
        └─────── nuevo camino ───────► E
```

Permite explorar alternativas sin eliminar completamente la estructura de la solución existente.

---

## 2. Reemplazo de segmento

Selecciona dos nodos de una ruta y busca un camino alternativo entre ellos.

```text
Original

A → B → C → D → E
    └─────────┘

Nueva

A → B → F → G → D → E
```

Este operador permite modificar regiones internas de una ruta.

---

## 3. Atajo

Busca conexiones directas entre nodos no consecutivos.

```text
A → B → C → D → E
    └─────────► D
```

Si existe el enlace directo, los nodos intermedios pueden eliminarse:

```text
A → B → D → E
```

Esto favorece la aparición de rutas más cortas cuando la topología lo permite.

---

# Dominancia de Pareto

Una solución `A` domina a una solución `B` cuando:

1. `A` no es peor que `B` en ninguno de los objetivos.
2. `A` es estrictamente mejor en al menos uno.

El archivo Pareto conserva únicamente soluciones que no son dominadas por otras soluciones conocidas.

---

# Gestión del frente de Pareto

Durante la ejecución se mantiene un archivo externo con las mejores soluciones encontradas.

La actualización realiza:

```text
Nuevas soluciones
       │
       ▼
Combinar con Pareto actual
       │
       ▼
Eliminar rutas duplicadas
       │
       ▼
Eliminar objetivos duplicados
       │
       ▼
Eliminar soluciones dominadas
       │
       ▼
Controlar tamaño mediante crowding
       │
       ▼
Frente Pareto actualizado
```

La **distancia de crowding** permite conservar soluciones distribuidas en diferentes regiones del espacio objetivo cuando el frente crece demasiado.

---

# Población inicial

La población inicial está formada únicamente por rutas:

```text
válidas + diferentes
```

El algoritmo intenta generar el número solicitado de rutas únicas antes de comenzar las iteraciones.

Esto evita iniciar la búsqueda con múltiples abejas representando exactamente la misma solución.

---

# Reproducibilidad

La implementación permite definir una semilla:

```python
abc = ABCMultiobjetivo(
    G,
    origen,
    destino,
    num_abejas=30,
    max_iteraciones=250,
    seed=42
)
```

La semilla controla los generadores aleatorios utilizados durante la búsqueda.

Esto permite repetir experimentos bajo las mismas condiciones.

---

# Flujo general del algoritmo

```text
                Dataset QoS
                     │
                     ▼
               Grafo dirigido
                     │
                     ▼
          Generación de población
            inicial de rutas
                     │
                     ▼
              Evaluación QoS
                     │
                     ▼
          Frente Pareto inicial
                     │
                     ▼
        ┌─────────────────────────┐
        │      Iteraciones ABC    │
        │                         │
        │  Abejas obreras         │
        │          ↓              │
        │  Generación de vecinos  │
        │          ↓              │
        │  Abejas espectadoras    │
        │          ↓              │
        │  Selección Pareto       │
        │          ↓              │
        │  Abejas exploradoras    │
        │          ↓              │
        │  Control de estancamiento│
        └────────────┬────────────┘
                     │
                     ▼
          Actualización del Pareto
                     │
                     ▼
             Frente Pareto final
```

---

# Historial de ejecución

Durante cada iteración se registran indicadores que permiten analizar el comportamiento del algoritmo, entre ellos:

| Indicador | Descripción |
|---|---|
| Tamaño Pareto | Número de soluciones no dominadas |
| Población única | Número de rutas diferentes |
| Diversidad de rutas | Diferencia estructural entre soluciones |
| Mejor latencia | Menor latencia encontrada |
| Mejor pérdida | Menor pérdida encontrada |
| Mejor jitter | Menor jitter encontrado |
| Mejor ancho de banda | Mayor ancho de banda encontrado |
| Intentos sin mejora | Nivel de estancamiento de la población |

Esto permite analizar no solamente los mejores valores encontrados, sino también la evolución de la diversidad y del frente de Pareto.

---

# Resultado

La ejecución devuelve:

```python
frente_pareto = abc.ejecutar()
```

Cada elemento contiene:

```python
(ruta, fitness)
```

Por ejemplo:

```python
for ruta, fitness in frente_pareto:
    metricas = abc.fitness_para_mostrar(fitness)

    print("Ruta:", ruta)
    print("Latencia:", metricas["Latencia"])
    print("Pérdida:", metricas["Perdida"])
    print("Jitter:", metricas["Jitter"])
    print("Ancho de banda:", metricas["AnchoBanda"])
```

El resultado final corresponde a un conjunto de rutas no dominadas que representan diferentes compromisos entre las métricas QoS.

---

# Principales mejoras respecto a la versión inicial

| Versión inicial | Versión mejorada |
|---|---|
| Suma directa de métricas para guiar rutas | Métricas normalizadas para orientar la búsqueda |
| Pérdida acumulada mediante suma | Probabilidad extremo a extremo |
| Ancho de banda tratado directamente | Ancho de banda como cuello de botella |
| Operadores genéricos | Operadores especializados para rutas |
| Reparación frecuente de soluciones | Generación directa de rutas válidas |
| Selección simple por dominancia | Ranking Pareto + crowding |
| Exploradoras generadas periódicamente | Exploradoras activadas por estancamiento |
| Aleatoriedad global | Semilla controlada |
| Menor control de duplicados | Población y Pareto con control de duplicados |
| Historial basado en un valor agregado | Seguimiento individual de métricas y diversidad |

---

## Tecnologías utilizadas

- Python
- NetworkX
- NumPy
- Pandas
- Matplotlib
- Artificial Bee Colony
- Optimización multiobjetivo
- Dominancia de Pareto

---

<div align="center">

### ABC Multiobjetivo para optimización de rutas QoS

La solución busca mantener un equilibrio entre **calidad**, **diversidad** y **exploración del espacio de rutas**.

</div>