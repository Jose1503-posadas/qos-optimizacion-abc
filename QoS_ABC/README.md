# Optimización de QoS en Redes de Telecomunicaciones usando ABC Multiobjetivo

Es un algoritmo de optimización multiobjetivo basado en **Artificial Bee Colony (ABC)** para encontrar rutas óptimas en redes de telecomunicaciones, considerando métricas de Calidad de Servicio (QoS).

---

## Objetivo
Optimizar rutas en un grafo dirigido considerando simultáneamente:
- Latencia (minimizar)
- Pérdida de paquetes (minimizar)
- Jitter (minimizar)
- Ancho de banda (maximizar)

El resultado es un **frente de Pareto de soluciones no dominadas**.

---

## Representación del problema

El sistema se modela como un grafo dirigido usando NetworkX:

- Nodos → dispositivos de red  
- Aristas → enlaces con métricas QoS  
- Ruta → solución candidata  

Cada solución se evalúa como un vector:

\[
Fitness = (Latencia,\ Pérdida,\ Jitter,\ Ancho\ de\ Banda)
\]

---

##  Algoritmo ABC Multiobjetivo

El algoritmo simula una colonia de abejas con tres roles:

### Abejas obreras
Exploran soluciones vecinas mediante:
- Reemplazar nodos
- Insertar nodos
- Eliminar nodos

---

### Abejas espectadoras
Seleccionan soluciones prometedoras usando dominancia de Pareto.

---

### Abejas exploradoras
Generan rutas aleatorias para evitar estancamiento.

---

## Evaluación de soluciones

Cada ruta generada es evaluada mediante la función evaluar, la cual calcula las métricas QoS acumuladas de la siguiente manera:
```python
fitness = abc.evaluar(ruta)
print(fitness)
```

De las cuales se obtienen el total independiente de cada métrica 

---

## Frente de Pareto
El resultado final del algoritmo es un conjunto de soluciones no dominadas:

```python
for ruta, fitness in frente_pareto:
    print("Ruta:", ruta)
    print("Fitness:", fitness)
```

El conjunto de soluciones obtenidas en el frente de Pareto representa diferentes compromisos entre los objetivos de QoS. Esto significa que cada ruta optimizada mejora algunos criterios a costa de otros.

---

## Análisis de convergencia

Durante la ejecución del algoritmo se almacena la evolución del mejor valor global del frente de Pareto. Esto permite analizar la convergencia del algoritmo a lo largo de las iteraciones.

La gráfica permite observar si el algoritmo converge o se estanca durante la optimización.

---

## Flujo del algoritmo

El proceso general del algoritmo es el siguiente:

1. Inicialización de rutas aleatorias en la red
2. Evaluación de métricas QoS
3. Construcción del frente de Pareto
4. Iteración del algoritmo:
  4.1 Abejas obreras → exploración local
  4.2 Abejas espectadoras → explotación de soluciones prometedoras
  4.3 Abejas exploradoras → diversificación
5. Actualización del frente de Pareto
6. Retorno de soluciones óptimas

---

## Resultado

El algoritmo devuelve:

- Un frente de Pareto con rutas óptimas
- Métricas QoS asociadas a cada ruta
- Evolución del proceso de optimización

---
