import random
import numpy as np
import networkx as nx


class MultiObjectiveABC:

    def __init__(self, G, source, target,
                 num_bees=30,
                 max_iter=100):

        self.G = G
        self.source = source
        self.target = target

        self.num_bees = num_bees
        self.max_iter = max_iter

        self.MAX_PARETO = 50

        self.population = []
        self.pareto_front = []

        self.history = []

        self.initialize_population()

    # =====================================================
    # Selección probabilística guiada por QoS
    # =====================================================

    def edge_cost(self, u, v):

        e = self.G[u][v]

        return (
            e["Latencia"] +
            e["PaquetesPerdidos"] +
            e["jitter"] +
            e["AnchoBanda"]
        )


    def weighted_neighbor_choice(self, current, visited):

        neighbors = [
            n for n in self.G.successors(current)
            if n not in visited
        ]

        if not neighbors:
            return None

        costs = []

        for n in neighbors:
            c = self.edge_cost(current, n)
            costs.append(1/(1+c))

        probs = np.array(costs)/sum(costs)

        return np.random.choice(neighbors, p=probs)


    # =====================================================
    # Generación de rutas
    # =====================================================

    def random_path(self, max_attempts=100):

        for _ in range(max_attempts):

            path = [self.source]
            current = self.source

            while current != self.target:

                nxt = self.weighted_neighbor_choice(
                    current,
                    path
                )

                if nxt is None:
                    break

                path.append(nxt)
                current = nxt

            if current == self.target:
                return path

        return None


    def initialize_population(self):

        while len(self.population) < self.num_bees:

            p = self.random_path()

            if p is None:
                continue

            if p not in self.population:
                self.population.append(p)


    # =====================================================
    # Evaluación
    # =====================================================

    def evaluate(self, path):

        latency = 0
        loss = 0
        jitter = 0
        bandwidth = 0

        for i in range(len(path)-1):

            u = path[i]
            v = path[i+1]

            if not self.G.has_edge(u, v):
                return None

            edge = self.G[u][v]

            latency += edge["Latencia"]
            loss += edge["PaquetesPerdidos"]
            jitter += edge["jitter"]
            bandwidth += edge["AnchoBanda"]

        return (
            latency,
            loss,
            jitter,
            bandwidth
        )


    # =====================================================
    # Pareto
    # =====================================================

    def dominates(self, a, b):

        return (
            all(x <= y for x, y in zip(a, b))
            and
            any(x < y for x, y in zip(a, b))
        )


    def crowding_distance(self, front):

        n = len(front)

        if n <= 2:
            return [float("inf")] * n

        distances = np.zeros(n)

        m = len(front[0][1])

        for obj in range(m):

            idx = sorted(
                range(n),
                key=lambda i: front[i][1][obj]
            )

            distances[idx[0]] = float("inf")
            distances[idx[-1]] = float("inf")

            fmin = front[idx[0]][1][obj]
            fmax = front[idx[-1]][1][obj]

            if fmax == fmin:
                continue

            for i in range(1, n-1):

                prev_val = front[idx[i-1]][1][obj]
                next_val = front[idx[i+1]][1][obj]

                distances[idx[i]] += (
                    (next_val-prev_val)
                    /
                    (fmax-fmin)
                )

        return distances


    def update_pareto(self, candidate):

        new_front = []

        dominated = False

        for sol, fit in self.pareto_front:

            if np.allclose(
                    fit,
                    candidate[1],
                    atol=1e-6):
                return

            if self.dominates(
                    candidate[1],
                    fit):
                continue

            if self.dominates(
                    fit,
                    candidate[1]):
                dominated = True

            new_front.append(
                (sol, fit)
            )

        if not dominated:
            new_front.append(candidate)

        if len(new_front) > self.MAX_PARETO:

            distances = self.crowding_distance(
                new_front
            )

            order = np.argsort(
                distances
            )[::-1]

            new_front = [
                new_front[i]
                for i in order[:self.MAX_PARETO]
            ]

        self.pareto_front = new_front


    # =====================================================
    # Vecindario
    # =====================================================

    def is_valid_path(self, path):

        for i in range(len(path)-1):

            if not self.G.has_edge(
                    path[i],
                    path[i+1]):
                return False

        return True


    def repair(self, path):

        if not self.is_valid_path(path):
            return self.random_path()

        current = path[-1]

        while current != self.target:

            nxt = self.weighted_neighbor_choice(
                current,
                path
            )

            if nxt is None:
                return self.random_path()

            path.append(nxt)

            current = nxt

        return path


    def neighbor(self, path):

        if len(path) <= 2:
            return path

        new_path = path[:]

        op = random.choice(
            [
                "replace",
                "insert",
                "delete"
            ]
        )

        if op == "replace":

            i = random.randint(
                1,
                len(path)-2
            )

            prev = new_path[i-1]

            nxt = self.weighted_neighbor_choice(
                prev,
                new_path
            )

            if nxt:
                new_path[i] = nxt


        elif op == "insert":

            i = random.randint(
                0,
                len(path)-2
            )

            prev = new_path[i]

            nxt = self.weighted_neighbor_choice(
                prev,
                new_path
            )

            if nxt:
                new_path.insert(
                    i+1,
                    nxt
                )


        elif (
            op == "delete"
            and
            len(path) > 3
        ):

            i = random.randint(
                1,
                len(path)-2
            )

            del new_path[i]

        return self.repair(
            new_path
        )


    # =====================================================
    # Selección
    # =====================================================

    def selection_probabilities(
            self,
            population):

        fits = [
            self.evaluate(p)
            for p in population
        ]

        scores = []

        for i, fi in enumerate(fits):

            score = 0

            for j, fj in enumerate(fits):

                if i == j:
                    continue

                if self.dominates(
                        fi,
                        fj):
                    score += 1

            scores.append(
                score+1
            )

        probs = np.array(
            scores
        )/sum(scores)

        return probs


    # =====================================================
    # Run
    # =====================================================

    def run(self):

        for iteration in range(
                self.max_iter):

            new_population = []

            # employed
            for sol in self.population:

                new_sol = self.neighbor(
                    sol
                )

                fit = self.evaluate(
                    new_sol
                )

                if fit is None:
                    continue

                new_population.append(
                    new_sol
                )

                self.update_pareto(
                    (
                        new_sol,
                        fit
                    )
                )

            if not new_population:
                continue

            # onlookers
            probs = self.selection_probabilities(
                new_population
            )

            onlookers = []

            for _ in range(
                    len(new_population)):

                idx = np.random.choice(
                    len(new_population),
                    p=probs
                )

                sol = new_population[idx]

                new_sol = self.neighbor(
                    sol
                )

                fit = self.evaluate(
                    new_sol
                )

                if fit:
                    onlookers.append(
                        new_sol
                    )
                    self.update_pareto(
                        (
                            new_sol, fit
                        )
                    )

            # scouts
            scouts = []

            for _ in range(
                    int(
                        0.1 *
                        self.num_bees)):

                p = self.random_path()

                if p:
                    scouts.append(
                        p
                    )

            self.population = (
                new_population + onlookers + scouts
            )

            self.population = list(
                {
                tuple(p): p
                    for p in self.population
                }.values()
            )

            self.population = self.population[
                :self.num_bees
            ]

            self.history.append(
                len(
                    self.pareto_front
                )
            )

        return self.pareto_front