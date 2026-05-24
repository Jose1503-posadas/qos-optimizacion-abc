# Optimización Multiobjetivo de QoS en Redes de Telecomunicaciones mediante el Algoritmo Artificial Bee Colony (ABC)

## Descripción del Proyecto

Este proyecto implementa un enfoque de optimización multiobjetivo para mejorar la Calidad de Servicio (QoS) en redes de telecomunicaciones utilizando el algoritmo bioinspirado Artificial Bee Colony (ABC).

La red es modelada como un grafo dirigido de libre escala, donde cada enlace posee métricas asociadas de:

* Latencia
* Jitter
* Pérdida de paquetes
* Ancho de banda

El objetivo consiste en encontrar rutas eficientes entre un nodo origen y un nodo destino considerando simultáneamente múltiples criterios de QoS y obteniendo un conjunto de soluciones no dominadas mediante optimización de Pareto.

---

## Autores
### José Alberto Posadas Gudiño
Universidad Autónoma Metropolitana (UAM-Cuajimalpa)

### Dr. Edwin Montes Orozco
Departamento de Ingeniería

### Dr. Abel García Nájera
Departamento de Matemáticas Aplicadas y Sistemas
Universidad Autónoma Metropolitana (UAM-Cuajimalpa)

---
## Objetivo General
Desarrollar e implementar un algoritmo Artificial Bee Colony Multiobjetivo capaz de optimizar simultáneamente métricas de Calidad de Servicio en redes de telecomunicaciones, generando un Frente de Pareto que permita identificar soluciones de compromiso entre objetivos conflictivos.

---

## Problema de Optimización
Se consideran cuatro funciones objetivo:

### Minimizar
* Latencia total
* Pérdida de paquetes
* Jitter

### Maximizar

* Ancho de banda disponible
Debido al conflicto natural entre estos objetivos, el problema se formula como una optimización multiobjetivo basada en dominancia de Pareto.

---

## Metodología
### 1. Generación de la Red
La topología se genera utilizando redes de libre escala (Scale-Free Networks), modeladas mediante grafos dirigidos.
Cada enlace contiene atributos de QoS:

* Ancho de banda
* Latencia
* Jitter
* Pérdida de paquetes

---
### 2. Normalización
Los parámetros son normalizados al intervalo [0,1] para evitar sesgos entre métricas con diferentes escalas.

---

### 3. Algoritmo Artificial Bee Colony
Se implementan tres tipos de agentes:

* Abejas Obreras
* Abejas Espectadoras
* Abejas Exploradoras

Cada abeja representa una posible ruta entre el nodo origen y el nodo destino.

---

### 4. Optimización Multiobjetivo

La calidad de una solución se evalúa mediante:

* Dominancia de Pareto
* Distancia de hacinamiento (distancia entre soluciones).
Esto permite conservar diversidad dentro del frente de soluciones.

---

### 5. Frente de Pareto

Las mejores soluciones no dominadas son almacenadas en un archivo Pareto que representa las rutas con distintos compromisos entre QoS.

---

## Tecnologías Utilizadas

* Python 3
* NetworkX
* NumPy
* Pandas
* Matplotlib

---

## Estructura del Proyecto

```text
ProyectoQoSABC/
│
├── GeneracionDataset/
      ├── GeneracionDataset.py
      ├── NormalizacionDataset.py
      ├── README.md
├── Red_datasets/
      ├── DatasetRed.csv
      ├── DatasetRed_Normalizado.csv
      ├── ParetoResultados.csv
      ├── README.md
├── QoS-ABC/
      ├── ABC_Algoritmo.py
      ├── README.md
├── VisualizacionDataset/
      ├── VisualizarRed.py
      ├── topologia_red.py
      ├── README.md
├── main.py
│
├── README.md
│
```

## Ejecución

---

## Resultados

El algoritmo produce:

* Frente de Pareto
* Rutas óptimas
* Valores de QoS asociados
* Visualización de la red
* Métricas de desempeño

Ejemplo de salida:

```text
Ruta:
0 → 19 → 17 → 20

Latencia: 1.2928
Pérdida: 0.8168
Jitter: 1.1714
Ancho de banda: 1.0978
```

---

## Artículo Asociado

Este repositorio forma parte del trabajo de investigación:
"Optimización de la Calidad de Servicio (QoS) en Redes de Telecomunicaciones Mediante el Algoritmo de Colonia de Abejas Artificiales"

---

