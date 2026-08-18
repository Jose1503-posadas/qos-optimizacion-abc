import random
import numpy as np
import networkx as nx


class ABCMultiobjetivo:
    def __init__(self, G, origen, destino, num_abejas, max_iteraciones):
        self.G = G
        self.origen = origen
        self.destino = destino
        self.num_abejas = num_abejas
        self.max_iteraciones = max_iteraciones
        self.MAX_PARETO = 50
        self.MAX_LONGITUD_RUTA = 25
        self.poblacion = []
        self.frente_pareto = []
        self.historial = []
        self.inicializar_poblacion()

    # Selección probabilística guiada por QoS
    def costo_arista(self, u, v):
        arista = self.G[u][v]
        return ( arista["Latencia"] + arista["PaquetesPerdidos"] + arista["jitter"] + arista["AnchoBanda"]
        )

    def elegir_vecino_probabilistico(self, actual, visitados):
        vecinos = [n for n in self.G.successors(actual)
                      if n not in visitados]
        if not vecinos:
            return None

        costos = []
        for n in vecinos:
            c = self.costo_arista(actual, n)
            costos.append(1 / (c + 1e-9))
        suma = sum(costos)
        if suma == 0:
            return random.choice(vecinos)

        probabilidades = np.array(costos)/suma
        return np.random.choice( vecinos, p=probabilidades)

    # generación de ruta
    def ruta_aleatoria(self, max_intentos=100):
        for _ in range(max_intentos):
            ruta = [self.origen]
            actual = self.origen
            while actual != self.destino:
                if len(ruta) >= self.MAX_LONGITUD_RUTA:
                    break
                siguiente = self.elegir_vecino_probabilistico(actual,ruta)
                if siguiente is None:
                    break
                ruta.append(siguiente)
                actual = siguiente
            if actual == self.destino:
                return ruta
        return None

    def inicializar_poblacion(self):
        while len(self.poblacion) < self.num_abejas:
            ruta = self.ruta_aleatoria()
            if ruta is None:
                continue
            if ruta not in self.poblacion:
                self.poblacion.append(ruta)

    # Evaluación
    def evaluar(self, ruta):
        latencia = 0
        perdida = 0
        jitter = 0
        ancho_banda = 0

        for i in range(len(ruta) - 1):
            u = ruta[i]
            v = ruta[i + 1]
            if not self.G.has_edge(u, v):
                return None
            arista = self.G[u][v]
            latencia += arista["Latencia"]
            perdida += arista["PaquetesPerdidos"]
            jitter += arista["jitter"]
            ancho_banda = max(ancho_banda,arista["AnchoBanda"])
        return(latencia,perdida,jitter,ancho_banda)

    # pareto
    def domina(self, a, b):
        return(all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b)))

    def distancia_entre_soluciones(self, frente):
        n = len(frente)
        if n <= 2:
            return [float("inf")] * n
        distancias = np.zeros(n)
        m = len(frente[0][1])

        for objetivo in range(m):
            indices = sorted(range(n),key=lambda i: frente[i][1][objetivo])
            distancias[indices[0]] = float("inf")
            distancias[indices[-1]] = float("inf")
            minimo = frente[indices[0]][1][objetivo]
            maximo = frente[indices[-1]][1][objetivo]
            if maximo == minimo:
                continue

            for i in range(1, n - 1):
                valor_prev = frente[indices[i - 1]][1][objetivo]
                valor_sig = frente[indices[i + 1]][1][objetivo]
                distancias[indices[i]] += ((valor_sig - valor_prev)/(maximo - minimo))
        return distancias

    def actualizar_pareto(self, candidato):
        nuevo_frente = []
        dominado = False
        for solucion, fitness in self.frente_pareto:
            if np.allclose(fitness,candidato[1],atol=1e-6):
                return

            if self.domina(candidato[1],fitness):
                continue

            if self.domina(fitness,candidato[1]):
                dominado = True

            nuevo_frente.append((solucion, fitness))

        if not dominado:
            nuevo_frente.append(candidato)

        if len(nuevo_frente) > self.MAX_PARETO:
            distancias = self.distancia_entre_soluciones(nuevo_frente)
            orden = np.argsort(distancias)[::-1]
            nuevo_frente = [nuevo_frente[i] for i in orden[:self.MAX_PARETO]]
        self.frente_pareto = nuevo_frente

    # Vecindario
    def es_ruta_valida(self, ruta):
        for i in range(len(ruta) - 1):
            if not self.G.has_edge( ruta[i], ruta[i + 1]):
                return False
        return True

    def reparar(self, ruta):
        if not self.es_ruta_valida(ruta):
            return self.ruta_aleatoria()
        actual = ruta[-1]
        visitados = set(ruta)
        while actual != self.destino:
            if len(ruta) >= self.MAX_LONGITUD_RUTA:
                return self.ruta_aleatoria()
            siguiente = self.elegir_vecino_probabilistico(actual, visitados)

            if siguiente is None:
                return self.ruta_aleatoria()

            ruta.append(siguiente)
            visitados.add(siguiente)
            actual = siguiente
        return ruta

    def vecino(self, ruta):
        if len(ruta) <= 2:
            return ruta

        nueva_ruta = ruta[:]
        operacion = random.choice(["reemplazar","insertar","eliminar"])
        
        if operacion == "reemplazar":
            i = random.randint(1, len(ruta) - 2)
            previo = nueva_ruta[i - 1]
            vecinos = list(self.G.successors(previo))
            vecinos = [ v for v in vecinos if v not in nueva_ruta]
            if vecinos:
                nueva_ruta[i] = random.choice(vecinos)
            # recortar desde el punto modificado
            nueva_ruta = nueva_ruta[:i + 1]

        elif operacion == "insertar":
            i = random.randint(0,len(ruta) - 2)
            previo = nueva_ruta[i]
            siguiente = self.elegir_vecino_probabilistico(previo,nueva_ruta)
            if siguiente:
                nueva_ruta.insert(i + 1, siguiente)

        elif ( operacion == "eliminar" and len(ruta) > 3):
            i = random.randint(1, len(ruta) - 2)
            del nueva_ruta[i]

        return self.reparar(nueva_ruta)


    # selección
    def probabilidades_seleccion( self,poblacion):
        fitnesses = [self.evaluar(r) for r in poblacion ]
        puntajes = []

        for i, fi in enumerate(fitnesses):
            if fi is None:
                puntajes.append(1)
                continue

            puntaje = 0

            for j, fj in enumerate(fitnesses):
                if i == j or fj is None:
                    continue

                if self.domina( fi,fj):
                    puntaje += 1

            puntajes.append( puntaje + 1)

        probabilidades = np.array(puntajes)/ sum(puntajes)

        return probabilidades

    # Ejecución principal
    def ejecutar(self):
        for iteracion in range(self.max_iteraciones):
            nueva_poblacion = []
            # Abejas obreras
            for solucion in self.poblacion:
                nueva_solucion = self.vecino(solucion)
                fitness = self.evaluar(nueva_solucion)

                if fitness is None:
                    continue

                nueva_poblacion.append(nueva_solucion)
                self.actualizar_pareto((nueva_solucion,fitness))

            if not nueva_poblacion:
                continue

            # Abejas espectadoras
            probabilidades = self.probabilidades_seleccion(nueva_poblacion)
            espectadoras = []
            for _ in range(len(nueva_poblacion)):
                indice = np.random.choice(len(nueva_poblacion), p=probabilidades)
                solucion = nueva_poblacion[indice]
                nueva_solucion = self.vecino(solucion)
                fitness = self.evaluar(nueva_solucion)
                if fitness is not None:
                    espectadoras.append(nueva_solucion)
                    self.actualizar_pareto((nueva_solucion,fitness))

            # Abejas exploradoras
            exploradoras = []
            for _ in range(int(0.1 * self.num_abejas)):
                ruta = self.ruta_aleatoria()
                if ruta:exploradoras.append(ruta)

            self.poblacion = (nueva_poblacion + espectadoras + exploradoras)
            self.poblacion = list({tuple(r): r for r in self.poblacion}.values())
            self.poblacion = self.poblacion[:self.num_abejas]

            # Guardar mejor valor global del frente
            if self.frente_pareto:
                mejor_valor = min(sum(fitness) for _, fitness in self.frente_pareto)
                self.historial.append(mejor_valor)

        return self.frente_pareto

    def es_mejor(self, fitness_nuevo, fitness_actual):
        return self.domina(fitness_nuevo,fitness_actual)