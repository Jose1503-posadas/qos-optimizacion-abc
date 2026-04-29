import csv
import networkx as nx
import random
import numpy as np

def generarRed(n=50, m=2):
        G = nx.barabasi_albert_graph(n, m) #red de libre_escala
        G = G.to_directed()

        for u, v in G.edges():
            #  (Ancho de Banda 10 - 200 Mbps)
            bw = random.uniform(10, 200)

            #  Latencia (1 - 100 ms + efecto de congestión)
            base_latencia = random.uniform(1, 100)
            latencia = base_latencia + (1 / bw) * 100

            # Jitter (dependiente de la latencia)
            jitter = random.uniform(0, 5) + 0.1 * latencia

            # Paquetes perdidos (< 1% típico + efecto de ancho de banda)
            loss = random.uniform(0.0001, 0.01) + (1 / bw) * 0.05

            # Asignar atributos
            G[u][v]['AnchoBanda'] = bw
            G[u][v]['latencia'] = latencia
            G[u][v]['jitter'] = jitter
            G[u][v]['PaquetesPerdidos'] = loss

        return G


def exportar_Red_a_ArchivoCSV(G, filename="DatasetRed.csv"):
    with open(filename, mode='w', newline='') as file:
        EscribeDoc = csv.writer(file)

        EscribeDoc.writerow(["Origen", "Destino", "AnchoBanda", "Latencia", "jitter", "PaquetesPerdidos"])

        for u, v, data in G.edges(data=True):
            EscribeDoc.writerow([
                u,
                v,
                data['AnchoBanda'],
                data['latencia'],
                data['jitter'],
                data['PaquetesPerdidos']
            ])
