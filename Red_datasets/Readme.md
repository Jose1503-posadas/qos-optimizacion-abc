# Datasets de la Red QoS

Esta carpeta contiene los conjuntos de datos generados para el análisis y optimización de Calidad de Servicio (QoS) en redes de telecomunicaciones.

## Archivos

### `DatasetRed.csv`

Contiene los datos originales generados a partir de la red sintética creada con el modelo de Barabási-Albert.

Cada registro representa un enlace de la red e incluye las siguientes métricas:

- Nodo origen
- Nodo destino
- Ancho de banda
- Latencia
- Jitter
- Pérdida de paquetes

Los valores se encuentran en su escala original.

---

### `DatasetRed_Normalizado.csv`

Contiene el mismo conjunto de datos después del proceso de normalización Min-Max.

Las métricas QoS fueron transformadas al rango `[0,1]` para facilitar su utilización en algoritmos de optimización y análisis multicriterio.

Además:

- El ancho de banda fue invertido para convertirlo en una métrica de minimización.
- Todas las métricas mantienen una escala uniforme.

---

## FitnessResultados.csv

Este archivo contiene los resultados obtenidos tras la ejecución del algoritmo de optimización multiobjetivo basado en Colonia de Abejas Artificiales (ABC).

---

El archivo almacena la evolución del mejor valor encontrado en cada iteración del algoritmo, representado mediante:

- `Iteracion`: número de iteración del algoritmo.
- `MejorFitness`: mejor valor escalar obtenido a partir del frente de Pareto en cada iteración.

---
