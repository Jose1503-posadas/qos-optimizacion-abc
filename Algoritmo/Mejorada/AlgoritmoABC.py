import math
import random
from typing import Iterable, List, Optional, Sequence, Tuple

import networkx as nx
import numpy as np


Ruta = List[int]
Fitness = Tuple[float, float, float, float]
Solucion = Tuple[Ruta, Fitness]


class ABCMultiobjetivo:
    """ABC multiobjetivo discreto para enrutamiento QoS.

    Convención de objetivos (todos se minimizan internamente):
      f1 = latencia total
      f2 = pérdida extremo-a-extremo = 1 - Π(1-p_e)
      f3 = jitter acumulado
      f4 = - ancho de banda de cuello de botella

    El grafo debe contener atributos CRUDOS por arista:
      Latencia, PaquetesPerdidos, jitter, AnchoBanda
    """

    def __init__(
        self,
        G: nx.DiGraph,
        origen: int,
        destino: int,
        num_abejas: int = 30,
        max_iteraciones: int = 100,
        max_pareto: int = 100,
        max_longitud_ruta: int = 25,
        limite: Optional[int] = None,
        seed: Optional[int] = None,
        prob_exploracion_constructor: float = 0.35,
        prob_aceptar_no_dominada: float = 0.20,
    ):
        if origen not in G or destino not in G:
            raise ValueError("Origen y destino deben existir en el grafo.")
        if origen == destino:
            raise ValueError("Origen y destino deben ser diferentes.")
        if not nx.has_path(G, origen, destino):
            raise ValueError(f"No existe ruta entre {origen} y {destino}.")
        if num_abejas < 4:
            raise ValueError("num_abejas debe ser al menos 4.")

        self.G = G
        self.origen = origen
        self.destino = destino
        self.num_abejas = num_abejas
        self.max_iteraciones = max_iteraciones
        self.MAX_PARETO = max_pareto
        self.MAX_LONGITUD_RUTA = max_longitud_ruta
        self.LIMITE = limite if limite is not None else max(10, 2 * num_abejas)
        self.prob_exploracion_constructor = prob_exploracion_constructor
        self.prob_aceptar_no_dominada = prob_aceptar_no_dominada

        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)

        self.poblacion: List[Ruta] = []
        self.intentos_sin_mejora: List[int] = []
        self.frente_pareto: List[Solucion] = []
        self.historial = []

        # Para heurística de construcción. La evaluación Pareto usa datos crudos.
        self._rangos = self._calcular_rangos_aristas()
        self._pueden_llegar_destino = nx.ancestors(self.G, self.destino) | {self.destino}

        self.inicializar_poblacion()
        self.actualizar_pareto((r, self.evaluar(r)) for r in self.poblacion)

    # ------------------------------------------------------------------
    # Utilidades de métricas y dominancia
    # ------------------------------------------------------------------
    def _calcular_rangos_aristas(self):
        nombres = ["Latencia", "PaquetesPerdidos", "jitter", "AnchoBanda"]
        rangos = {}
        for nombre in nombres:
            vals = [float(d[nombre]) for _, _, d in self.G.edges(data=True)]
            rangos[nombre] = (min(vals), max(vals))
        return rangos

    @staticmethod
    def _normalizar(valor: float, minimo: float, maximo: float) -> float:
        if math.isclose(maximo, minimo):
            return 0.0
        return (valor - minimo) / (maximo - minimo)

    def vector_costo_arista(self, u: int, v: int) -> np.ndarray:
        """Vector [0,1] sólo para guiar construcción/mutación, no para Pareto."""
        d = self.G[u][v]
        lat = self._normalizar(float(d["Latencia"]), *self._rangos["Latencia"])
        loss = self._normalizar(float(d["PaquetesPerdidos"]), *self._rangos["PaquetesPerdidos"])
        jit = self._normalizar(float(d["jitter"]), *self._rangos["jitter"])
        bw_norm = self._normalizar(float(d["AnchoBanda"]), *self._rangos["AnchoBanda"])
        bw_cost = 1.0 - bw_norm
        return np.array([lat, loss, jit, bw_cost], dtype=float)

    def costo_arista(self, u: int, v: int, pesos: Optional[np.ndarray] = None) -> float:
        if pesos is None:
            pesos = np.full(4, 0.25)
        return float(np.dot(pesos, self.vector_costo_arista(u, v)))

    @staticmethod
    def domina(a: Sequence[float], b: Sequence[float], eps: float = 1e-12) -> bool:
        no_peor = all(x <= y + eps for x, y in zip(a, b))
        mejor_en_algo = any(x < y - eps for x, y in zip(a, b))
        return no_peor and mejor_en_algo

    def evaluar(self, ruta: Ruta) -> Fitness:
        if not self.es_ruta_valida(ruta):
            raise ValueError(f"Ruta inválida: {ruta}")

        latencia = 0.0
        prob_entrega = 1.0
        jitter = 0.0
        cuello_botella = float("inf")

        for u, v in zip(ruta[:-1], ruta[1:]):
            d = self.G[u][v]
            latencia += float(d["Latencia"])
            p = float(d["PaquetesPerdidos"])
            p = min(max(p, 0.0), 1.0)
            prob_entrega *= (1.0 - p)
            jitter += float(d["jitter"])
            cuello_botella = min(cuello_botella, float(d["AnchoBanda"]))

        perdida_extremo_extremo = 1.0 - prob_entrega
        return (latencia, perdida_extremo_extremo, jitter, -cuello_botella)

    # ------------------------------------------------------------------
    # Generación de rutas con diversidad
    # ------------------------------------------------------------------
    def _pesos_aleatorios(self) -> np.ndarray:
        # Una escalarización distinta por construcción evita sesgo permanente
        # hacia una única suma de objetivos.
        return self.np_rng.dirichlet(np.ones(4))

    def elegir_vecino_probabilistico(
        self,
        actual: int,
        visitados: Iterable[int],
        pesos: np.ndarray,
        epsilon: Optional[float] = None,
        destino_objetivo: Optional[int] = None,
    ) -> Optional[int]:
        visitados = set(visitados)
        vecinos = [n for n in self.G.successors(actual) if n not in visitados]

        if destino_objetivo == self.destino or destino_objetivo is None:
            vecinos = [n for n in vecinos if n in self._pueden_llegar_destino]

        if not vecinos:
            return None

        if epsilon is None:
            epsilon = self.prob_exploracion_constructor

        # epsilon-greedy: una fracción de decisiones es deliberadamente aleatoria.
        if self.rng.random() < epsilon:
            return self.rng.choice(vecinos)

        costos = np.array([self.costo_arista(actual, n, pesos) for n in vecinos], dtype=float)
        # Softmax sobre costo. Temperatura relativamente alta = menos avaricia.
        temperatura = 0.35
        z = -(costos - costos.min()) / max(temperatura, 1e-12)
        desirability = np.exp(z)
        probs = desirability / desirability.sum()
        idx = int(self.np_rng.choice(len(vecinos), p=probs))
        return vecinos[idx]

    def _camino_aleatorio(
        self,
        inicio: int,
        fin: int,
        prohibidos: Optional[Iterable[int]] = None,
        max_nodos: Optional[int] = None,
        max_intentos: int = 25,
        exploracion: Optional[float] = None,
    ) -> Optional[Ruta]:
        prohibidos_base = set(prohibidos or [])
        prohibidos_base.discard(inicio)
        prohibidos_base.discard(fin)
        max_nodos = max_nodos or self.MAX_LONGITUD_RUTA

        for _ in range(max_intentos):
            pesos = self._pesos_aleatorios()
            ruta = [inicio]
            visitados = set(prohibidos_base) | {inicio}
            actual = inicio

            while actual != fin and len(ruta) < max_nodos:
                siguiente = self.elegir_vecino_probabilistico(
                    actual,
                    visitados,
                    pesos,
                    epsilon=exploracion,
                    destino_objetivo=fin,
                )
                if siguiente is None:
                    break
                ruta.append(siguiente)
                visitados.add(siguiente)
                actual = siguiente

            if actual == fin:
                return ruta

        # Fallback: camino válido con una escalarización Pareto aleatoria.
        permitidos = set(self.G.nodes) - prohibidos_base
        permitidos.update([inicio, fin])
        H = self.G.subgraph(permitidos)
        if inicio not in H or fin not in H or not nx.has_path(H, inicio, fin):
            return None

        pesos = self._pesos_aleatorios()
        try:
            ruta = nx.shortest_path(
                H,
                inicio,
                fin,
                weight=lambda u, v, d: self.costo_arista(u, v, pesos),
            )
        except nx.NetworkXNoPath:
            return None

        if len(ruta) <= max_nodos and len(ruta) == len(set(ruta)):
            return list(ruta)
        return None

    def ruta_aleatoria(self, max_intentos: int = 100) -> Optional[Ruta]:
        for intento in range(max_intentos):
            # Parte de la población se genera casi uniforme y parte guiada por QoS.
            if intento % 2 == 0:
                exploracion = 0.70
            else:
                exploracion = self.prob_exploracion_constructor
            ruta = self._camino_aleatorio(
                self.origen,
                self.destino,
                max_nodos=self.MAX_LONGITUD_RUTA,
                max_intentos=3,
                exploracion=exploracion,
            )
            if ruta is not None:
                return ruta
        return None

    def inicializar_poblacion(self):
        vistas = set()
        max_intentos = self.num_abejas * 300

        for _ in range(max_intentos):
            if len(self.poblacion) >= self.num_abejas:
                break
            ruta = self.ruta_aleatoria()
            if ruta is None:
                continue
            clave = tuple(ruta)
            if clave not in vistas:
                vistas.add(clave)
                self.poblacion.append(ruta)

        if len(self.poblacion) < self.num_abejas:
            raise RuntimeError(
                f"Sólo se pudieron generar {len(self.poblacion)} rutas únicas de "
                f"{self.num_abejas}. Reduce num_abejas/MAX_LONGITUD_RUTA o revisa la conectividad."
            )

        self.intentos_sin_mejora = [0] * len(self.poblacion)

    # ------------------------------------------------------------------
    # Vecindario discreto: todos los operadores intentan producir rutas válidas
    # ------------------------------------------------------------------
    def es_ruta_valida(self, ruta: Sequence[int]) -> bool:
        if not ruta or ruta[0] != self.origen or ruta[-1] != self.destino:
            return False
        if len(ruta) > self.MAX_LONGITUD_RUTA:
            return False
        if len(ruta) != len(set(ruta)):
            return False
        return all(self.G.has_edge(u, v) for u, v in zip(ruta[:-1], ruta[1:]))

    def _desviar_sufijo(self, ruta: Ruta) -> Optional[Ruta]:
        if len(ruta) <= 2:
            return self.ruta_aleatoria()

        # No cortar siempre cerca del inicio: conserva parte de la fuente actual.
        corte = self.rng.randint(1, len(ruta) - 2)
        prefijo = ruta[: corte + 1]
        max_sufijo = self.MAX_LONGITUD_RUTA - len(prefijo) + 1
        sufijo = self._camino_aleatorio(
            prefijo[-1],
            self.destino,
            prohibidos=prefijo[:-1],
            max_nodos=max_sufijo,
            exploracion=0.45,
        )
        if sufijo is None:
            return None
        nueva = prefijo[:-1] + sufijo
        return nueva if self.es_ruta_valida(nueva) and nueva != ruta else None

    def _reemplazar_segmento(self, ruta: Ruta) -> Optional[Ruta]:
        if len(ruta) < 4:
            return self._desviar_sufijo(ruta)

        i = self.rng.randint(0, len(ruta) - 3)
        j = self.rng.randint(i + 2, len(ruta) - 1)
        inicio, fin = ruta[i], ruta[j]

        # Evitar reutilizar nodos del resto de la ruta para impedir ciclos.
        prohibidos = set(ruta[:i] + ruta[j + 1 :])
        max_segmento = min(
            self.MAX_LONGITUD_RUTA - (len(ruta) - (j - i + 1)) + 1,
            max(3, (j - i + 1) + 4),
        )
        segmento = self._camino_aleatorio(
            inicio,
            fin,
            prohibidos=prohibidos,
            max_nodos=max_segmento,
            exploracion=0.55,
        )
        if segmento is None:
            return None

        nueva = ruta[:i] + segmento + ruta[j + 1 :]
        return nueva if self.es_ruta_valida(nueva) and nueva != ruta else None

    def _atajo(self, ruta: Ruta) -> Optional[Ruta]:
        if len(ruta) < 4:
            return None

        pares = []
        for i in range(len(ruta) - 2):
            for j in range(i + 2, len(ruta)):
                if self.G.has_edge(ruta[i], ruta[j]):
                    pares.append((i, j))
        if not pares:
            return None

        i, j = self.rng.choice(pares)
        nueva = ruta[: i + 1] + ruta[j:]
        return nueva if self.es_ruta_valida(nueva) and nueva != ruta else None

    def vecino(self, ruta: Ruta) -> Ruta:
        operadores = [self._desviar_sufijo, self._reemplazar_segmento, self._atajo]
        self.rng.shuffle(operadores)
        for op in operadores:
            nueva = op(ruta)
            if nueva is not None:
                return nueva
        return ruta.copy()

    # ------------------------------------------------------------------
    # Archivo Pareto y diversidad
    # ------------------------------------------------------------------
    @staticmethod
    def distancia_crowding(frente: Sequence[Solucion]) -> np.ndarray:
        n = len(frente)
        if n == 0:
            return np.array([])
        if n <= 2:
            return np.full(n, np.inf)

        objetivos = np.array([fit for _, fit in frente], dtype=float)
        m = objetivos.shape[1]
        dist = np.zeros(n, dtype=float)

        for obj in range(m):
            orden = np.argsort(objetivos[:, obj])
            dist[orden[0]] = np.inf
            dist[orden[-1]] = np.inf
            minimo = objetivos[orden[0], obj]
            maximo = objetivos[orden[-1], obj]
            rango = maximo - minimo
            if math.isclose(rango, 0.0):
                continue
            for k in range(1, n - 1):
                if np.isinf(dist[orden[k]]):
                    continue
                prev_ = objetivos[orden[k - 1], obj]
                next_ = objetivos[orden[k + 1], obj]
                dist[orden[k]] += (next_ - prev_) / rango
        return dist

    def actualizar_pareto(self, candidatos: Iterable[Solucion]):
        # Unir archivo + candidatos, eliminando duplicados por ruta.
        por_ruta = {tuple(r): (list(r), fit) for r, fit in self.frente_pareto}
        for ruta, fit in candidatos:
            por_ruta[tuple(ruta)] = (list(ruta), tuple(float(x) for x in fit))

        soluciones = list(por_ruta.values())

        # Eliminar duplicados prácticamente idénticos en espacio objetivo.
        unicas = []
        claves_obj = set()
        for ruta, fit in soluciones:
            clave = tuple(round(x, 12) for x in fit)
            if clave in claves_obj:
                continue
            claves_obj.add(clave)
            unicas.append((ruta, fit))

        no_dominadas = []
        for i, sol_i in enumerate(unicas):
            fit_i = sol_i[1]
            if any(
                j != i and self.domina(sol_j[1], fit_i)
                for j, sol_j in enumerate(unicas)
            ):
                continue
            no_dominadas.append(sol_i)

        if len(no_dominadas) > self.MAX_PARETO:
            crowd = self.distancia_crowding(no_dominadas)
            orden = np.argsort(crowd)[::-1][: self.MAX_PARETO]
            no_dominadas = [no_dominadas[int(i)] for i in orden]

        self.frente_pareto = no_dominadas

    def _novedad_objetiva(self, fitness: Fitness) -> float:
        if len(self.frente_pareto) < 2:
            return float("inf")

        A = np.array([f for _, f in self.frente_pareto], dtype=float)
        x = np.array(fitness, dtype=float)
        minimo = A.min(axis=0)
        maximo = A.max(axis=0)
        rango = np.where(np.isclose(maximo - minimo, 0.0), 1.0, maximo - minimo)
        A_n = (A - minimo) / rango
        x_n = (x - minimo) / rango
        d = np.linalg.norm(A_n - x_n, axis=1)
        # Si x coincide con un punto del archivo, usar la segunda distancia.
        d_orden = np.sort(d)
        return float(d_orden[1] if len(d_orden) > 1 and d_orden[0] < 1e-12 else d_orden[0])

    def _aceptar_candidato(self, actual: Ruta, candidato: Ruta) -> bool:
        if candidato == actual:
            return False

        # Evitar colapso de la población por rutas duplicadas. El archivo Pareto
        # puede conservar la calidad global sin convertir toda la colonia en clones.
        clave = tuple(candidato)
        if any(tuple(r) == clave and r != actual for r in self.poblacion):
            return False

        f_actual = self.evaluar(actual)
        f_candidato = self.evaluar(candidato)

        if self.domina(f_candidato, f_actual):
            return True
        if self.domina(f_actual, f_candidato):
            return False

        # Si son mutuamente no dominadas, privilegiar regiones menos pobladas,
        # pero mantener una pequeña probabilidad de movimiento lateral.
        nov_actual = self._novedad_objetiva(f_actual)
        nov_candidato = self._novedad_objetiva(f_candidato)
        if nov_candidato > nov_actual + 1e-12:
            return True
        return self.rng.random() < self.prob_aceptar_no_dominada

    # ------------------------------------------------------------------
    # Selección de espectadoras: rango Pareto + crowding + piso uniforme
    # ------------------------------------------------------------------
    def _frentes_no_dominados(self, soluciones: Sequence[Solucion]):
        n = len(soluciones)
        domina_a = [set() for _ in range(n)]
        dominado_por = [0] * n
        frentes = [[]]

        for p in range(n):
            for q in range(n):
                if p == q:
                    continue
                if self.domina(soluciones[p][1], soluciones[q][1]):
                    domina_a[p].add(q)
                elif self.domina(soluciones[q][1], soluciones[p][1]):
                    dominado_por[p] += 1
            if dominado_por[p] == 0:
                frentes[0].append(p)

        i = 0
        while i < len(frentes) and frentes[i]:
            siguiente = []
            for p in frentes[i]:
                for q in domina_a[p]:
                    dominado_por[q] -= 1
                    if dominado_por[q] == 0:
                        siguiente.append(q)
            if siguiente:
                frentes.append(siguiente)
            i += 1
        return frentes

    def probabilidades_seleccion(self) -> np.ndarray:
        soluciones = [(r, self.evaluar(r)) for r in self.poblacion]
        frentes = self._frentes_no_dominados(soluciones)
        calidad = np.zeros(len(soluciones), dtype=float)

        for rango, indices in enumerate(frentes, start=1):
            sub = [soluciones[i] for i in indices]
            crowd = self.distancia_crowding(sub)
            finitos = crowd[np.isfinite(crowd)]
            max_finito = float(finitos.max()) if len(finitos) else 1.0
            crowd = np.where(np.isinf(crowd), max_finito + 1.0, crowd)
            if crowd.max() > 0:
                crowd = crowd / crowd.max()
            for local, idx in enumerate(indices):
                calidad[idx] = math.exp(-0.8 * (rango - 1)) * (1.0 + 0.35 * crowd[local])

        if calidad.sum() <= 0:
            return np.full(len(soluciones), 1.0 / len(soluciones))

        p_dirigida = calidad / calidad.sum()
        # 20% de selección uniforme evita monopolio de unas pocas fuentes.
        p_uniforme = np.full(len(soluciones), 1.0 / len(soluciones))
        return 0.80 * p_dirigida + 0.20 * p_uniforme

    # ------------------------------------------------------------------
    # Historial: no colapsar 4 objetivos en una suma escalar
    # ------------------------------------------------------------------
    @staticmethod
    def _diversidad_rutas(rutas: Sequence[Ruta]) -> float:
        if len(rutas) < 2:
            return 0.0
        distancias = []
        for i in range(len(rutas)):
            e1 = set(zip(rutas[i][:-1], rutas[i][1:]))
            for j in range(i + 1, len(rutas)):
                e2 = set(zip(rutas[j][:-1], rutas[j][1:]))
                union = e1 | e2
                sim = len(e1 & e2) / len(union) if union else 1.0
                distancias.append(1.0 - sim)
        return float(np.mean(distancias)) if distancias else 0.0

    def _registrar_historial(self, iteracion: int):
        if not self.frente_pareto:
            return
        fitnesses = np.array([f for _, f in self.frente_pareto], dtype=float)
        self.historial.append(
            {
                "Iteracion": iteracion,
                "TamanoPareto": len(self.frente_pareto),
                "PoblacionUnica": len({tuple(r) for r in self.poblacion}),
                "DiversidadRutas": self._diversidad_rutas(self.poblacion),
                "MejorLatencia": float(fitnesses[:, 0].min()),
                "MejorPerdida": float(fitnesses[:, 1].min()),
                "MejorJitter": float(fitnesses[:, 2].min()),
                "MejorAnchoBanda": float((-fitnesses[:, 3]).max()),
                "PromedioIntentosSinMejora": float(np.mean(self.intentos_sin_mejora)),
            }
        )

    # ------------------------------------------------------------------
    # Ejecución ABC
    # ------------------------------------------------------------------
    def ejecutar(self):
        for iteracion in range(1, self.max_iteraciones + 1):
            candidatos_archivo: List[Solucion] = []

            # 1) Abejas obreras: cada fuente compite con su vecina.
            for i in range(self.num_abejas):
                actual = self.poblacion[i]
                candidato = self.vecino(actual)
                fit_candidato = self.evaluar(candidato)
                candidatos_archivo.append((candidato, fit_candidato))

                if self._aceptar_candidato(actual, candidato):
                    self.poblacion[i] = candidato
                    self.intentos_sin_mejora[i] = 0
                else:
                    self.intentos_sin_mejora[i] += 1

            self.actualizar_pareto(candidatos_archivo)

            # 2) Abejas espectadoras: selección probabilística con diversidad.
            probabilidades = self.probabilidades_seleccion()
            candidatos_archivo = []
            for _ in range(self.num_abejas):
                i = int(self.np_rng.choice(self.num_abejas, p=probabilidades))
                actual = self.poblacion[i]
                candidato = self.vecino(actual)
                fit_candidato = self.evaluar(candidato)
                candidatos_archivo.append((candidato, fit_candidato))

                if self._aceptar_candidato(actual, candidato):
                    self.poblacion[i] = candidato
                    self.intentos_sin_mejora[i] = 0
                else:
                    self.intentos_sin_mejora[i] += 1

            self.actualizar_pareto(candidatos_archivo)

            # 3) Abejas exploradoras: sólo abandonan fuentes estancadas.
            scouts = []
            existentes = {tuple(r) for r in self.poblacion}
            for i, intentos in enumerate(self.intentos_sin_mejora):
                if intentos < self.LIMITE:
                    continue

                nueva = None
                for _ in range(50):
                    candidata = self.ruta_aleatoria()
                    if candidata is not None and tuple(candidata) not in existentes:
                        nueva = candidata
                        break
                if nueva is not None:
                    existentes.discard(tuple(self.poblacion[i]))
                    self.poblacion[i] = nueva
                    existentes.add(tuple(nueva))
                    self.intentos_sin_mejora[i] = 0
                    scouts.append((nueva, self.evaluar(nueva)))

            if scouts:
                self.actualizar_pareto(scouts)

            # El archivo siempre considera también la población vigente.
            self.actualizar_pareto((r, self.evaluar(r)) for r in self.poblacion)
            self._registrar_historial(iteracion)

        return self.frente_pareto

    @staticmethod
    def fitness_para_mostrar(fitness: Fitness):
        """Convierte f4=-BW al ancho de banda positivo para reportes."""
        return {
            "Latencia": fitness[0],
            "Perdida": fitness[1],
            "Jitter": fitness[2],
            "AnchoBanda": -fitness[3],
        }