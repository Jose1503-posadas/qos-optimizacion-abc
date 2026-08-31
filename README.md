# Optimización Multiobjetivo de QoS en Redes de Telecomunicaciones mediante Artificial Bee Colony

---

# Descripción del proyecto

Este proyecto implementa un algoritmo de optimización multiobjetivo basado en **Artificial Bee Colony (ABC)** para encontrar rutas eficientes dentro de una red de telecomunicaciones considerando múltiples métricas de Calidad de Servicio (**QoS**).

La red se representa mediante un grafo dirigido donde:

```text
Nodos   → dispositivos
Aristas → enlaces de comunicación
Ruta    → solución posible
```

Cada enlace contiene información relacionada con:

- Latencia.
- Pérdida de paquetes.
- Jitter.
- Ancho de banda.

Debido a que estos objetivos pueden entrar en conflicto, el algoritmo no busca una única solución óptima.

En su lugar construye un **frente de Pareto**, formado por diferentes rutas no dominadas que representan compromisos entre las métricas QoS.

---

# Objetivo general

Desarrollar e implementar un algoritmo **Artificial Bee Colony Multiobjetivo** capaz de optimizar simultáneamente diferentes métricas de Calidad de Servicio en una red de telecomunicaciones.

El algoritmo busca proporcionar un conjunto de rutas no dominadas que permitan seleccionar diferentes alternativas dependiendo de las necesidades de comunicación de la red.

---

# Problema de optimización

Se consideran cuatro objetivos:

| Métrica | Objetivo |
|---|---|
| Latencia | Minimizar |
| Pérdida de paquetes | Minimizar |
| Jitter | Minimizar |
| Ancho de banda | Maximizar |

Para una ruta:

```text
Origen → Nodo1 → Nodo2 → ... → Destino
```

las métricas se calculan de la siguiente manera.

---

## Latencia

La latencia total corresponde a la suma de las latencias de todos los enlaces de la ruta:

$$
L(R) = \sum_{e \in R} L_e
$$

---

## Pérdida de paquetes

La pérdida se calcula como una probabilidad extremo a extremo:

$$
P_{\text{loss}}(R) =
1-\prod_{e \in R}(1-p_e)
$$

Esto representa la probabilidad de que ocurra una pérdida durante el recorrido completo de la ruta.

---

## Jitter

El jitter se acumula a lo largo de los enlaces:

$$
J(R) = \sum_{e \in R} J_e
$$

---

## Ancho de banda

El ancho de banda disponible de una ruta está limitado por su enlace con menor capacidad.

Por ello se utiliza el **cuello de botella**:

$$
BW(R) = \min_{e \in R}(BW_e)
$$

---

# Optimización multiobjetivo

Internamente los cuatro objetivos se manejan como problemas de minimización.

El ancho de banda utiliza signo negativo:

$$
Fitness(R) =
\left(
Latencia,\;
Pérdida,\;
Jitter,\;
-AnchoBanda
\right)
$$

De esta manera puede utilizarse una única definición de dominancia de Pareto.

Una solución `A` domina a una solución `B` cuando:

1. `A` no es peor que `B` en ningún objetivo.
2. `A` es estrictamente mejor en al menos uno.

Las soluciones que no son dominadas forman el **frente de Pareto**.

---

# Topología de red

La red utilizada en los experimentos es una red sintética basada en el modelo **Barabási-Albert**.

Este modelo genera una estructura de libre escala donde algunos nodos presentan una mayor cantidad de conexiones que otros.

Posteriormente la topología se representa como un grafo dirigido y se asignan métricas QoS independientes a los enlaces.

Cada enlace contiene:

```text
Origen
Destino
AnchoBanda
Latencia
jitter
PaquetesPerdidos
```

Los datasets utilizados se encuentran en:

```text
Red_datasets/
```

---

# Normalización de las métricas

En la versión final **no se utiliza un dataset previamente normalizado para evaluar las rutas**.

Las métricas reales se utilizan directamente para:

```text
Evaluación de rutas
Dominancia de Pareto
Resultados experimentales
```

La normalización Min-Max se utiliza únicamente dentro del algoritmo para orientar algunos procesos de construcción y modificación de rutas:

$$
x' =
\frac{x-x_{\min}}
{x_{\max}-x_{\min}}
$$

Esto permite comparar métricas con escalas diferentes durante la búsqueda sin modificar los valores reales utilizados para evaluar las soluciones.

> La versión original y los archivos normalizados se conservan dentro del repositorio para documentar la evolución del proyecto.

---

# Algoritmo Artificial Bee Colony

El algoritmo se basa en el comportamiento de una colonia artificial de abejas. Se utilizan tres tipos principales:

---

## Abejas obreras

Las abejas obreras mantienen soluciones actuales y exploran rutas vecinas.

La versión mejorada incorpora operadores diseñados específicamente para modificar rutas de red:

```text
- Desvío de sufijo
- Reemplazo de segmento
- Atajo
```

Estos operadores permiten generar nuevas rutas manteniendo su validez y evitando ciclos.

---

## Abejas espectadoras

Las abejas espectadoras seleccionan soluciones de la población considerando:

- Nivel de dominancia.
- Frente Pareto.
- Distancia de crowding.
- Exploración probabilística.

Esto permite favorecer soluciones de calidad sin concentrar completamente la búsqueda en una sola región.

---

## Abejas exploradoras

Cada solución mantiene un contador de intentos sin mejora. Cuando una abeja permanece estancada durante suficientes intentos, su ruta puede ser reemplazada por una nueva solución.

Esto permite introducir diversidad y explorar nuevas regiones del espacio de búsqueda.

---

# Principales mejoras implementadas

Durante el desarrollo se conservó la implementación inicial con el objetivo de documentar claramente la evolución del algoritmo.

Entre las principales modificaciones se encuentran:

| Versión inicial | Versión mejorada |
|---|---|
| Métricas con escalas diferentes utilizadas directamente en la guía | Normalización interna para orientar la búsqueda |
| Pérdida acumulada mediante suma | Probabilidad extremo a extremo |
| Ancho de banda calculado incorrectamente | Cuello de botella de la ruta |
| Tratamiento homogéneo incorrecto del ancho de banda | Maximización mediante `-AnchoBanda` |
| Operadores genéricos | Operadores especializados para rutas |
| Reparación frecuente de rutas | Mayor generación directa de rutas válidas |
| Selección simple | Ranking Pareto y crowding |
| Menor control de duplicados | Control de rutas y objetivos repetidos |
| Aleatoriedad global | Generadores controlados mediante semilla |
| Exploradores periódicos | Exploradores activados por estancamiento |
| Historial basado en un único valor | Seguimiento individual de métricas y diversidad |

La implementación completa de ambas versiones se encuentra en:

```text
Algoritmo/
```

---

# Estructura del proyecto

```text
qos-optimizacion-abc/
│
├── Algoritmo/
│   ├── Original/
│   │   └── AlgoritmoABC.py
│   │
│   ├── Mejorada/
│   │   └── AlgoritmoABC.py
│   │
│   └── README.md
│
├── Ejecucion/
│   ├── Original/
│   │
│   ├── Mejorada/
│   │   ├── 01_VerificarRutasMetricas.py
│   │   ├── 02_VerificarFrentePareto.py
│   │   ├── 03_VerificarOptimosExactos.py
│   │   ├── 04_ExperimentoIteraciones.py
│   │   ├── 05_VisualizarExperimentoIteraciones.py
│   │   ├── 06_ExperimentoMultiplesSemillas.py
│   │   ├── 07_VerificarReproducibilidad.py
│   │   ├── 08_VisualizarMultiplesSemillas.py
│   │   ├── 09_ConstruirFrenteReferencia.py
│   │   ├── 10_CompararOriginalMejorada.py
│   │   └── 11_VisualizarComparacion.py
|   |   └── 12_ExperimentoMultiplesPares.py
│   │
│   └── README.md
│
├── Red_datasets/
│   ├── Original/
│   └── Mejorada/
│       └── DatasetRed.csv
│
├── VisualizacionDataset/
│   ├── Original/
│   └── Mejorada/
│
├── Resultados/
│   ├── Mejorada/
│   │   ├── 01_Verificacion/
│   │   ├── 02_ExperimentoIteraciones/
│   │   ├── 03_MultiplesSemillas/
│   │   ├── 04_Reproducibilidad/
│   │   └── 05_FrenteReferencia/
│   │
│   ├── ComparacionOriginalMejorada/
│   │
│   └── README.md
│
└── README.md
```

# Documentación y guía del proyecto

El proyecto se encuentra dividido en distintas secciones, cada una acompañada de su propia documentación.El objetivo de estos archivos `README` no es únicamente describir el contenido de las carpetas, sino también explicar el proceso seguido durante el desarrollo del proyecto, desde la generación de la red hasta la ejecución y evaluación del algoritmo ABC.

De esta manera se puede consultar únicamente la sección que se necesite o seguir la documentación en orden para comprender el funcionamiento completo del proyecto.

---

### Implementación del algoritmo

```text
Algoritmo/README.md
```

Explica:

- funcionamiento del ABC
- evaluación QoS
- generación de rutas
- operadores de vecindario
- selección
- crowding
- frente de Pareto
- mejoras respecto a la implementación inicial.

---

### Ejecución

```text
Ejecucion/README.md
```

Describe:

- objetivo de cada experimento
- orden de ejecución
- archivos utilizados
- configuración experimental
- archivos generados

---

### Resultados

```text
Resultados/README.md
```

Contiene:

- resultados numéricos
- tablas
- gráficas
- interpretación de los experimentos
- comparación entre versiones
- conclusiones experimentales

---

# Requisitos

El proyecto utiliza:

```text
- Python 3
- NetworkX
- NumPy
- Pandas
- Matplotlib
```

Las dependencias pueden instalarse mediante:

```bash
pip install networkx numpy pandas matplotlib
```

---

# Ejecución del proyecto

Los comandos deben ejecutarse desde la carpeta raíz:

```text
qos-optimizacion-abc/
```

Por ejemplo:

```powershell
PS C:\...\qos-optimizacion-abc>
```

---

# Opción 1. Utilizar el dataset incluido

Para reproducir los experimentos realizados no es necesario generar una nueva red.

El dataset utilizado por la versión mejorada se encuentra en:

```text
Red_datasets/Mejorada/DatasetRed.csv
```

Por lo tanto, puede comenzarse directamente con los scripts de evaluación.

Esta es la opción recomendada para **reproducir los resultados del proyecto**.

---

# Opción 2. Generar una nueva red

También es posible generar una nueva topología y sus métricas QoS utilizando los scripts correspondientes de generación del dataset.

Los experimentos presentados en `Resultados/` corresponden específicamente al dataset incluido en el proyecto.

---

# Visualización de la topología

La carpeta:

```text
VisualizacionDataset/
```

contiene los scripts utilizados para representar gráficamente la red.

La visualización permite observar:

- nodos
- enlaces
- dirección de las conexiones
- nodos con mayor grado
- estructura general de la topología

---

# Ejecución experimental

La evaluación de la versión mejorada se encuentra dividida en diferentes etapas.

---

## 1. Verificar rutas y métricas

```powershell
python Ejecucion/Mejorada/01_VerificarRutasMetricas.py
```

Comprueba independientemente:

```text
- Validez de las rutas
- Latencia
- Pérdida
- Jitter
- Ancho de banda
```

---

## 2. Verificar el frente de Pareto

```powershell
python Ejecucion/Mejorada/02_VerificarFrentePareto.py
```

Comprueba:

```text
- Soluciones dominadas
- Rutas duplicadas
- Objetivos duplicados
```

---

## 3. Calcular óptimos individuales exactos

```powershell
python Ejecucion/Mejorada/03_VerificarOptimosExactos.py
```

Obtiene referencias exactas para:

```text
- Latencia
- Pérdida
- Jitter
-- Ancho de banda
```

Estos valores se utilizan posteriormente para calcular el gap de las soluciones encontradas.

---

## 4. Evaluar diferentes números de iteraciones

```powershell
python Ejecucion/Mejorada/04_ExperimentoIteraciones.py
```

Se prueban:

```text
25, 50, 100, 150, 250, 400
```

iteraciones utilizando diferentes semillas.

---

## 5. Visualizar el experimento de iteraciones

```powershell
python Ejecucion/Mejorada/05_VisualizarExperimentoIteraciones.py
```

Genera gráficas relacionadas con:

```text
- Éxito completo
- Tiempo promedio
- Tamaño del Pareto
- Diversidad
- Éxito por objetivo
```

---

## 6. Ejecutar múltiples semillas

Una vez seleccionadas las 250 iteraciones:

```powershell
python Ejecucion/Mejorada/06_ExperimentoMultiplesSemillas.py
```

Se realizan:

```text
30 ejecuciones
```

utilizando:

```text
Seeds = 1 ... 30
```

---

## 7. Verificar reproducibilidad

```powershell
python Ejecucion/Mejorada/07_VerificarReproducibilidad.py
```

Ejecuta dos veces la misma configuración con:

```text
Seed = 42
```

y compara los resultados.

---

## 8. Visualizar los resultados de múltiples semillas

```powershell
python Ejecucion/Mejorada/08_VisualizarMultiplesSemillas.py
```

Genera:

```text
- Éxito por objetivo
- Tamaño Pareto por seed
- Gap de ancho de banda
```

---

## 9. Construir el frente de referencia empírico

```powershell
python Ejecucion/Mejorada/09_ConstruirFrenteReferencia.py
```

Combina los frentes obtenidos durante las 30 ejecuciones y conserva únicamente las soluciones globalmente no dominadas.

---

## 10. Comparar versión Original y Mejorada

```powershell
python Ejecucion/Mejorada/10_CompararOriginalMejorada.py
```

Se realiza una comparación ilustrativa utilizando:

```text
Seed:         42
Origen:       52
Destino:      96
Abejas:       30
Iteraciones:  250
```

Las rutas de ambas implementaciones son reevaluadas mediante las mismas definiciones QoS para permitir una comparación común.

---

## 11. Visualizar la comparación

```powershell
python Ejecucion/Mejorada/11_VisualizarComparacion.py
```

Genera:

```text
-Comparación de gaps
- Comparación del tamaño Pareto
- Comparación del tiempo
```

##

## 12. Experimento con múltiples pares origen–destino

```powershell
python Ejecucion/Mejorada/12_ExperimentoMultiplesPares.py
```

Este experimento evalúa el comportamiento del algoritmo sobre distintos pares origen–destino de la red.


---

# Artículo asociado

Este repositorio forma parte del trabajo:

**“Optimización de la Calidad de Servicio (QoS) en Redes de Telecomunicaciones mediante el Algoritmo de Colonia de Abejas Artificiales”**

---