import math
import random
from typing import Iterable, List, Optional, Sequence, Tuple
import networkx as nx
import numpy as np

Ruta = List[int] 
Fitness = Tuple[float, float, float, float]
Solucion = Tuple[Ruta, Fitness]

class ABCMultiobjetivo:
    """ algoritmo ABC multiobjetivo para enrutamiento QoS"""

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
        self.LIMITE = (limite if limite is not None else max(10, 2 * num_abejas))
        self.prob_exploracion_constructor = (prob_exploracion_constructor)
        self.prob_aceptar_no_dominada = (prob_aceptar_no_dominada)

        # generadores de aleatorios
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
        # Población
        self.poblacion: List[Ruta] = []
        #número de intentos sin mejora por fuente
        self.intentos_sin_mejora: List[int] = []
        # Archivo Pareto
        self.frente_pareto: List[Solucion] = []
        # historial por iteración
        self.historial = []
        # rangos utilizados únicamente para guiar construcción y mutaciones.
        self._rangos = self._calcular_rangos_aristas()
        # Nodos desde los cuales existe posibilidad de llegar al destino.
        self._pueden_llegar_destino = (nx.ancestors(self.G, self.destino)| {self.destino})
        # inicialización
        self.inicializar_poblacion()
        # archivo Pareto inicial
        self.actualizar_pareto((r, self.evaluar(r)) for r in self.poblacion)

    def _calcular_rangos_aristas(self):
        """Calcula los rangos de cada métrica QoS en el grafo para normalización."""

        nombres = ["Latencia", "PaquetesPerdidos","jitter","AnchoBanda"]
        rangos = {}
        for nombre in nombres:
            vals = [float(d[nombre]) for _, _, d in self.G.edges(data=True)] # obtener los valores de la metrica 
            rangos[nombre] = (min(vals),max(vals))
        return rangos

    @staticmethod #
    def _normalizar(valor: float, minimo: float,maximo: float) -> float: 
        """normaliza un valor entre 0 y 1 dado un rango [minimo, maximo]"""
        if math.isclose(maximo, minimo):
            return 0.0

        return ((valor - minimo)/(maximo - minimo))

    #la normalización no se utiliza para el frente Pareto, solo para guiar la construcción y mutación de rutas.
    def vector_costo_arista(self,u: int,v: int) -> np.ndarray:
        """calcula el vector de costos normalizados de una arista (u, v) en el grafo G"""

        d = self.G[u][v]
        #normalza cada metrica 
        lat = self._normalizar(float(d["Latencia"]),*self._rangos["Latencia"])
        loss = self._normalizar(float(d["PaquetesPerdidos"]),*self._rangos["PaquetesPerdidos"])
        jit = self._normalizar(float(d["jitter"]),*self._rangos["jitter"])
        bw_norm = self._normalizar(float(d["AnchoBanda"]),*self._rangos["AnchoBanda"])

        #mucho ancho de banda = menor costo
        bw_cost = 1.0 - bw_norm

        return np.array([lat,loss,jit,bw_cost],dtype=float)

    def costo_arista(self,u: int,v: int,pesos: Optional[np.ndarray] = None) -> float:
        """calcula el costo ponderado de una arista (u, v) en el grafo G dado un vector de pesos"""

        if pesos is None:pesos = np.full(4, 0.25) # pesos por defecto

        return float(np.dot(pesos,self.vector_costo_arista(u, v)))

    @staticmethod
    def domina(a: Sequence[float],b: Sequence[float], eps: float = 1e-12) -> bool:
        """determina si la solución a domina a la solución b en el sentido de Pareto"""

        no_peor = all(x <= y + eps for x, y in zip(a, b)) # verifica que a no sea peor que b en ningún objetivo
        mejor_en_algo = any(x < y - eps for x, y in zip(a, b)) # verifica que a sea mejor que b en al menos un objetivo

        return (no_peor and mejor_en_algo)

    def evaluar(self, ruta: Ruta) -> Fitness:
        """Calcula el vector de metricas QoS de una ruta desde el origen hasta el destino."""
        
        if not self.es_ruta_valida(ruta): raise ValueError(f"Ruta inválida: {ruta}")

        latencia = 0.0
        prob_entrega = 1.0
        jitter = 0.0
        cuello_botella = float("inf")

        for u, v in zip(ruta[:-1],ruta[1:]):
            d = self.G[u][v]

            # Latencia acumulada
            latencia += float(d["Latencia"])
            # Probabilidad de pérdida
            p = float(d["PaquetesPerdidos"])
            p = min(max(p, 0.0),1.0)
            # Probabilidad de entrega completa
            prob_entrega *= (1.0 - p)
            # Jitter acumulado
            jitter += float(d["jitter"])
            # Ancho de banda cuello de botella
            cuello_botella = min(cuello_botella,float(d["AnchoBanda"]))

        perdida_extremo_extremo = (1.0 - prob_entrega)

        # se minimizan las metricas 
        return (latencia,perdida_extremo_extremo,jitter,-cuello_botella)

    def _pesos_aleatorios(self) -> np.ndarray:
        """Genera un vector de pesos aleatorio para las métricas QoS, que suman 1"""

        return self.np_rng.dirichlet(np.ones(4))

    def elegir_vecino_probabilistico(self,actual: int,visitados: Iterable[int],pesos: np.ndarray, epsilon: Optional[float] = None, destino_objetivo: Optional[int] = None,) -> Optional[int]:
        """elige un vecino del nodo actual basado en un enfo de QoS y una probabilidad de exploración epsilon"""

        visitados = set(visitados)

        vecinos = [n for n in self.G.successors(actual) if n not in visitados] #filtra vecinos que ya han sido visitados

        if (destino_objetivo == self.destino or destino_objetivo is None): #evitar nodos que no pueden llegar al destino final
            vecinos = [n for n in vecinos if n in self._pueden_llegar_destino]

        if not vecinos:
            return None

        if epsilon is None: epsilon = (self.prob_exploracion_constructor)

        if self.rng.random() < epsilon: #exploración aleatoria 
            return self.rng.choice(vecinos)

        #selección guiada por QoS
        costos = np.array([self.costo_arista(actual,n, pesos) for n in vecinos], dtype=float)
        temperatura = 0.35 # que tan aleatoria es la seleccion entre los vecinos 
        z = (-(costos - costos.min())/ max(temperatura, 1e-12))

        preferencias = np.exp(z) # convierte los costos en preferencias, donde menor costo = mayor preferencia
        probs = preferencias / preferencias.sum() # costos normalizados a probabilidades

        idx = int(self.np_rng.choice(len(vecinos),p=probs))

        return vecinos[idx]

    def _camino_aleatorio(self, inicio: int,fin: int, prohibidos: Optional[Iterable[int]] = None,max_nodos: Optional[int] = None, max_intentos: int = 25, exploracion: Optional[float] = None,) -> Optional[Ruta]:
        """genera una ruta aleatoria desde inicio hasta fin, evitando nodos prohibidos y respetando max_nodos"""

        prohibidos_base = set(prohibidos or [])
        prohibidos_base.discard(inicio)
        prohibidos_base.discard(fin)

        max_nodos = (max_nodos or self.MAX_LONGITUD_RUTA)

        #intentos aleatorios para encontrar una ruta
        for _ in range(max_intentos):
            pesos = (self._pesos_aleatorios())
            ruta = [inicio]
            visitados = (set(prohibidos_base)| {inicio})
            actual = inicio

            while (actual != fin and len(ruta) < max_nodos):
                siguiente = (self.elegir_vecino_probabilistico(actual, visitados, pesos, epsilon=exploracion,destino_objetivo=fin,))

                if siguiente is None:
                    break

                ruta.append(siguiente)
                visitados.add(siguiente)
                actual = siguiente

            if actual == fin:
                return ruta

        # Si los intentos aleatorios fallaron, se intenta encontrar un camino más guiado por QoS, evitando nodos prohibidos y respetando max_nodos.
        permitidos = (set(self.G.nodes)- prohibidos_base)
        permitidos.update([inicio,fin])
        H = self.G.subgraph(permitidos)

        if (inicio not in H or fin not in H or not nx.has_path(H,inicio,fin)): # no hay camino posible
            return None

        pesos = (self._pesos_aleatorios()) 

        try: # intenta encontrar el camino más corto basado en los costos ponderados de QoS
            ruta = nx.shortest_path(H,inicio,fin, weight=lambda u, v, d: self.costo_arista(u,v,pesos),)
        except nx.NetworkXNoPath:
            return None

        if (len(ruta) <= max_nodos and len(ruta) == len(set(ruta))): # verifica que la ruta no exceda max_nodos y que no tenga ciclos
            return list(ruta)

        return None

    def ruta_aleatoria(self, max_intentos: int = 100) -> Optional[Ruta]:
        """ genera una ruta aleatoria desde el origen hasta el destino, utilizando una combinación de exploración aleatoria y guiada por QoS."""

        for intento in range(max_intentos):
            if intento % 2 == 0: # cada dos intentos, se aumenta la exploración para diversificar las rutas generadas
                exploracion = 0.70
            else:
                exploracion = (self.prob_exploracion_constructor)

            # Genera una ruta desde el origen hasta el destino respetando la longitud máxima y el nivel de exploración definido
            ruta = (self._camino_aleatorio( self.origen, self.destino, max_nodos=self.MAX_LONGITUD_RUTA, max_intentos=3, exploracion=exploracion,))

            if ruta is not None:
                return ruta

        return None

    def inicializar_poblacion(self):
        """ genera la población inicial con rutas válidas y únicas entre el origen y el destino """

        vistas = set() # almacena rutas generadas - evitar duplicados 
        max_intentos = (self.num_abejas* 300)

        for _ in range(max_intentos):

            if (len(self.poblacion)>= self.num_abejas): #detiene la busqueda cuando alcanza el num de abejas
                break

            ruta = (self.ruta_aleatoria()) # nueva ruta

            if ruta is None:
                continue

            clave = tuple(ruta) # tupla - permite comparar 

            if clave not in vistas: # agrega si no existe 
                vistas.add(clave)
                self.poblacion.append(ruta)

        if (len(self.poblacion) < self.num_abejas): #verifica que se haya generado la poblacion correcta 

            raise RuntimeError(
                f"Sólo se pudieron generar "
                f"{len(self.poblacion)} rutas únicas de "
                f"{self.num_abejas}. "
                f"Reduce num_abejas/MAX_LONGITUD_RUTA "
                f"o revisa la conectividad."
            )

        self.intentos_sin_mejora = ([0]* len(self.poblacion))

    def es_ruta_valida(self, ruta: Sequence[int]) -> bool:
        """ Verifica que una ruta cumpla con las condiciones necesarias para ser utilizada dentro del algoritmo"""

        if (not ruta or ruta[0] != self.origen or ruta[-1] != self.destino): # verifica que la ruta exista, inicie en el origen y termine en el destino
            return False

        if (len(ruta) > self.MAX_LONGITUD_RUTA): # no supere longitud maxima 
            return False

        if (len(ruta) != len(set(ruta))): # no permite nodos repetidos 
            return False

        return all(self.G.has_edge(u, v) for u, v in zip( ruta[:-1],ruta[1:])) # nodo valido entre cada par 


    def _desviar_sufijo(self,ruta: Ruta) -> Optional[Ruta]:
        """modifica la parte final de una ruta manteniendo un prefijo y generando un nuevo camino desde un punto intermedio hasta el destino."""

        if len(ruta) <= 2: # nueva ruta si es corta 
            return (self.ruta_aleatoria())

        corte = self.rng.randint(1,len(ruta) - 2) # punto de corte aleatorio
        prefijo = ruta[:corte + 1] # conserva ruta parte inicial 
        max_sufijo = (self.MAX_LONGITUD_RUTA - len(prefijo) + 1) 
        sufijo = (self._camino_aleatorio(prefijo[-1],self.destino, prohibidos=prefijo[:-1], max_nodos=max_sufijo,exploracion=0.45,)) # evita los nodos ya utilizados

        if sufijo is None:
            return None

        nueva = (prefijo[:-1] + sufijo)

        if (self.es_ruta_valida(nueva) and nueva != ruta): # devuelve si es valida y diferente a la otra 
            return nueva

        return None

    def _reemplazar_segmento(self, ruta: Ruta) -> Optional[Ruta]:
        """reemplaza una sección intermedia de la ruta por un camino alternativo entre dos nodos seleccionados aleatoriamente"""

        if len(ruta) < 4: #desvia el sufijo en caso que la ruta sea muy corta 
            return (self._desviar_sufijo(ruta))

        i = self.rng.randint(0, len(ruta) - 3) # índice inicial del segmento que será reemplazado
        j = self.rng.randint(i + 2,len(ruta) - 1) # índice final dejando al menos un nodo entre ambos puntos

        #obtiene los nodos que delimitan el segmento a reemplazar
        inicio = ruta[i]
        fin = ruta[j]

        prohibidos = set(ruta[:i]+ ruta[j + 1:]) # evitar reutilizar nodos del resto de la ruta (evita ciclos)
        max_segmento = min(self.MAX_LONGITUD_RUTA - (len(ruta)- (j - i + 1))+ 1, max(3,(j - i + 1) + 4),)
        segmento = (self._camino_aleatorio(inicio, fin,prohibidos=prohibidos,max_nodos=max_segmento, exploracion=0.55,)) #camino alternativo entre los nodos inicio y fin

        if segmento is None:
            return None

        nueva = (ruta[:i]+ segmento+ ruta[j + 1:])

        if (self.es_ruta_valida(nueva) and nueva != ruta): #devuelve la nueva ruta si es válida y diferente de la original
            return nueva

        return None

    def _atajo( self, ruta: Ruta) -> Optional[Ruta]:
        """ Busca un enlace directo entre dos nodos no consecutivos de la ruta para eliminar nodos intermedios y generar una ruta más corta """

        if len(ruta) < 4:
            return None

        pares = []

        #recorre los nodos de la ruta buscando posibles atajos
        for i in range(len(ruta) - 2):
            for j in range(i + 2,len(ruta)):
                if self.G.has_edge(ruta[i], ruta[j]):
                    pares.append((i, j))

        if not pares:
            return None

        
        i, j = self.rng.choice(pares) #selecciona aleatoriamente uno de los atajos encontrados
        nueva = (ruta[:i + 1]+ ruta[j:]) #Elimina los nodos intermedios y conecta directamente los extremos del atajo

        if (self.es_ruta_valida(nueva) and nueva != ruta):
            return nueva

        return None

    def vecino(self, ruta: Ruta) -> Ruta:
        """Genera una ruta vecina usando uno de los operadores disponibles."""

        operadores = [self._desviar_sufijo, self._reemplazar_segmento, self._atajo]
        self.rng.shuffle(operadores)  # Cambia el orden para no favorecer siempre al mismo operador

        for op in operadores:
            nueva = op(ruta)
            if nueva is not None:
                return nueva

        return ruta.copy()

    @staticmethod
    def distancia_crowding(frente: Sequence[Solucion]) -> np.ndarray:
        """Calcula la distancia de crowding para mantener diversidad en el frente."""

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

            #los extremos siempre se conservan porque representan soluciones límite
            dist[orden[0]] = dist[orden[-1]] = np.inf

            minimo, maximo = objetivos[orden[0], obj], objetivos[orden[-1], obj]
            rango = maximo - minimo

            if math.isclose(rango, 0.0):
                continue

            for k in range(1, n - 1):
                idx = orden[k]

                if np.isinf(dist[idx]):
                    continue

                prev_ = objetivos[orden[k - 1], obj]
                next_ = objetivos[orden[k + 1], obj]
                dist[idx] += (next_ - prev_) / rango

        return dist

    def actualizar_pareto(self, candidatos: Iterable[Solucion]):
        """Actualiza el archivo Pareto con nuevas soluciones no dominadas."""

        #combina el Pareto actual y los candidatos, evitando rutas repetidas
        por_ruta = {
            tuple(r): (list(r), fit)
            for r, fit in self.frente_pareto
        }

        for ruta, fit in candidatos:
            por_ruta[tuple(ruta)] = (list(ruta), tuple(float(x) for x in fit))

        soluciones = list(por_ruta.values())

        #elimina soluciones que tienen exactamente los mismos objetivos
        unicas = []
        claves_obj = set()

        for ruta, fit in soluciones:
            clave = tuple(round(x, 12) for x in fit)

            if clave in claves_obj:
                continue

            claves_obj.add(clave)
            unicas.append((ruta, fit))

        # Conserva únicamente soluciones no dominadas
        no_dominadas = []

        for i, sol_i in enumerate(unicas):
            dominada = any(
                j != i and self.domina(sol_j[1], sol_i[1])
                for j, sol_j in enumerate(unicas)
            )

            if not dominada:
                no_dominadas.append(sol_i)

        #Si el Pareto crece demasiado, conserva las soluciones con mayor crowding
        if len(no_dominadas) > self.MAX_PARETO:
            crowd = self.distancia_crowding(no_dominadas)
            orden = np.argsort(crowd)[::-1][:self.MAX_PARETO]
            no_dominadas = [no_dominadas[int(i)] for i in orden]

        self.frente_pareto = no_dominadas


    def _novedad_objetiva(self, fitness: Fitness) -> float:
        """Mide qué tan diferente es una solución respecto al frente Pareto actual."""

        if len(self.frente_pareto) < 2:
            return float("inf")

        A = np.array([f for _, f in self.frente_pareto], dtype=float)
        x = np.array(fitness, dtype=float)

        minimo, maximo = A.min(axis=0), A.max(axis=0)

        # Evita división entre cero cuando un objetivo tiene el mismo valor en todo el Pareto
        rango = np.where(
            np.isclose(maximo - minimo, 0.0),
            1.0,
            maximo - minimo
        )

        # Normaliza objetivos para que ninguna métrica domine solo por su escala
        A_n = (A - minimo) / rango
        x_n = (x - minimo) / rango

        d_orden = np.sort(np.linalg.norm(A_n - x_n, axis=1))

        # Si coincide con una solución existente, usa la distancia al segundo punto más cercano
        if len(d_orden) > 1 and d_orden[0] < 1e-12:
            return float(d_orden[1])

        return float(d_orden[0])

    def _aceptar_candidato(self, actual: Ruta, candidato: Ruta) -> bool:
        """Determina si una nueva ruta debe reemplazar a la ruta actual."""

        if candidato == actual:
            return False

        #evita llenar la población con copias de una misma ruta
        clave = tuple(candidato)

        if any(
            tuple(r) == clave and r != actual
            for r in self.poblacion
        ):
            return False

        f_actual = self.evaluar(actual)
        f_candidato = self.evaluar(candidato)

        #si uno domina claramente al otro, la decisión es directa
        if self.domina(f_candidato, f_actual):
            return True

        if self.domina(f_actual, f_candidato):
            return False

        #si ninguno domina, se favorece al que aporte mayor novedad al Pareto
        nov_actual = self._novedad_objetiva(f_actual)
        nov_candidato = self._novedad_objetiva(f_candidato)

        if nov_candidato > nov_actual + 1e-12:
            return True

        #permite ocasionalmente movimientos laterales para mantener exploración
        return self.rng.random() < self.prob_aceptar_no_dominada


    def _frentes_no_dominados(self, soluciones: Sequence[Solucion]):
        """Separa las soluciones en frentes según su nivel de dominancia."""

        n = len(soluciones)
        domina_a = [set() for _ in range(n)]
        dominado_por = [0 for _ in range(n)]
        frentes = [[]]

        # Determina qué soluciones domina cada una y cuántas la dominan
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

        # Va liberando soluciones conforme desaparecen sus dominadores
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
        """Calcula la probabilidad de selección de cada ruta por las abejas espectadoras."""

        soluciones = [(r, self.evaluar(r)) for r in self.poblacion]
        frentes = self._frentes_no_dominados(soluciones)
        calidad = np.zeros(len(soluciones), dtype=float)

        for rango, indices in enumerate(frentes, start=1):
            sub = [soluciones[i] for i in indices]
            crowd = self.distancia_crowding(sub)

            # Sustituye los infinitos de los extremos por un valor superior al resto
            finitos = crowd[np.isfinite(crowd)]
            max_finito = float(finitos.max()) if len(finitos) else 1.0
            crowd = np.where(np.isinf(crowd), max_finito + 1.0, crowd)

            if crowd.max() > 0:
                crowd = crowd / crowd.max()

            # Mejor frente + mayor crowding = mayor probabilidad de ser seleccionada
            for local, idx in enumerate(indices):
                calidad[idx] = (
                    math.exp(-0.8 * (rango - 1))
                    * (1.0 + 0.35 * crowd[local])
                )

        if calidad.sum() <= 0:
            return np.full(len(soluciones), 1.0 / len(soluciones))

        p_dirigida = calidad / calidad.sum()
        p_uniforme = np.full(len(soluciones), 1.0 / len(soluciones))

        # 80 % selección guiada y 20 % exploración uniforme
        return 0.80 * p_dirigida + 0.20 * p_uniforme

    @staticmethod
    def _diversidad_rutas(rutas: Sequence[Ruta]) -> float:
            """Calcula la diversidad promedio entre rutas usando sus enlaces."""

            if len(rutas) < 2:
                return 0.0

            distancias = []

            for i in range(len(rutas)):
                e1 = set(zip(rutas[i][:-1], rutas[i][1:]))

                for j in range(i + 1, len(rutas)):
                    e2 = set(zip(rutas[j][:-1], rutas[j][1:]))
                    union = e1 | e2

                    # Similitud de Jaccard entre los enlaces utilizados por ambas rutas
                    sim = len(e1 & e2) / len(union) if union else 1.0
                    distancias.append(1.0 - sim)

            return float(np.mean(distancias)) if distancias else 0.0

    def _registrar_historial(self,iteracion: int):
        """ Registra el historial de la iteración actual del algoritmo ABC"""

        if not self.frente_pareto: # vacio
            return

        # convertir el fitness a array para poder calcular los minimos y maximos de cada objetivo
        fitnesses = np.array([f for _, f in self.frente_pareto],dtype=float)

        self.historial.append( #registra el historial de la iteracion actual 
            {
                "Iteracion":iteracion,
                "TamanoPareto":len(self.frente_pareto),
                "PoblacionUnica":len({tuple(r) for r in self.poblacion}),
                "DiversidadRutas":self._diversidad_rutas(self.poblacion),
                "MejorLatencia":float(fitnesses[:, 0].min()),
                "MejorPerdida":float(fitnesses[:, 1].min()),
                "MejorJitter":float(fitnesses[:, 2].min()),
                "MejorAnchoBanda":float((-fitnesses[:, 3]).max()),
                "PromedioIntentosSinMejora":float(np.mean(self.intentos_sin_mejora)),
            }
        )

    def ejecutar(self):
        """ Ejecuta el algoritmo ABC para optimizar rutas en el grafo G desde el nodo origen hasta el nodo destino"""

        for iteracion in range(1,self.max_iteraciones + 1):

            #abejas obreras que buscan rutas vecinas y las comparan con sus rutas actuales
            candidatos_archivo = []

            for i in range(self.num_abejas):

                actual = (self.poblacion[i]) 
                candidato = (self.vecino(actual)) 
                fit_candidato = (self.evaluar(candidato)) # calcula el fitness de la ruta candidata
                candidatos_archivo.append((candidato, fit_candidato))

                if self._aceptar_candidato(actual, candidato): 
                    self.poblacion[i] = (candidato) # reemplaza la ruta actual con la ruta candidata
                    self.intentos_sin_mejora[i] = 0 
                else:
                    self.intentos_sin_mejora[i] += 1

            self.actualizar_pareto(candidatos_archivo)

            #abejas espectadoras que seleccionan rutas de la población según las probabilidades de selección
            probabilidades = (self.probabilidades_seleccion())
            candidatos_archivo = []

            for _ in range(self.num_abejas):
                i = int(self.np_rng.choice(self.num_abejas, p=probabilidades)) # selecciona una abeja obrera de la población según las probabilidades de selección
                actual = (self.poblacion[i])
                candidato = (self.vecino(actual))
                fit_candidato = (self.evaluar(candidato))
                candidatos_archivo.append((candidato,fit_candidato)) # agrega la ruta candidata y su fitness al archivo de candidatos

                if self._aceptar_candidato(actual, candidato): 
                    self.poblacion[i] = (candidato) # reemplaza la ruta actual con la ruta candidata
                    self.intentos_sin_mejora[i] = 0 
                else:
                    self.intentos_sin_mejora[i] += 1 

            self.actualizar_pareto(candidatos_archivo)

            # - abejas exploradoras que encontraron nuevas rutas
            scouts = [] 

            existentes = {tuple(r) for r in self.poblacion} #conjunto de rutas existentes en la población

            for i, intentos in enumerate(self.intentos_sin_mejora):
                # si la abeja obrera ha fallado en mejorar su ruta durante demasiados intentos, se le asigna una nueva ruta exploradora
                if intentos < self.LIMITE:
                    continue

                nueva = None

                for _ in range(50):
                    candidata = (self.ruta_aleatoria())
                    if (candidata is not None and tuple(candidata) not in existentes):# ruta valida y no esta en la poblacion
                        nueva = candidata
                        break

                if nueva is not None:
                    existentes.discard(tuple(self.poblacion[i])) # elimina la ruta actual de la abeja obrera del conjunto de rutas existentes
                    self.poblacion[i] = (nueva) #actualiza la ruta de la abeja obrera con la nueva ruta exploradora

                    existentes.add(tuple(nueva))
                    self.intentos_sin_mejora[i] = 0
                    scouts.append((nueva, self.evaluar(nueva))) #agregar la nuea ruta

            if scouts: # si se encontraron nuevas rutas exploradoras
                self.actualizar_pareto(scouts)

            #actualiza el archivo de pareto 
            self.actualizar_pareto((r,self.evaluar(r)) for r in self.poblacion)

            #registrar historial
            self._registrar_historial(iteracion)

        return self.frente_pareto

    @staticmethod #solo recibe el fitness y no necesita acceder a la instancia de la clase
    def fitness_para_mostrar(fitness: Fitness):
        """Convierte el fitness de la ruta en un diccionario para mostrarlo de manera más legible"""
        return {"Latencia":fitness[0], "Perdida":fitness[1],"Jitter": fitness[2],"AnchoBanda":-fitness[3],}