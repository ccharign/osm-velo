# -*- coding:utf-8 -*-

import networkx as nx
from petites_fonctions import distance_euc



class Graphe_minimaliste():
    """
    Classe de graphe avec uniquement le graphe networkx. Pour être utilisé lors de la phase d’initialisation quamd aucune donnée n’a encore été obtenue.
    """
    
    def __init__(self, g):
        """ Entrée : g, MultiDiGraph de networkx"""
        self.multidigraphe = g
        print("Calcul de la version sans multiarêtes")
        self.digraphe = nx.DiGraph(g)  # ox.get_digraph(g)


    def __contains__(self, n):
        """ Indique si le nœud n est dans g"""
        return n in self.digraphe.nodes

    
    def voisins_nus(self, s):
        """ Itérateur sur les voisins de s, sans la longueur de l’arête."""
        return (t for t in self.digraphe[s].keys())

    
    def est_arête(self, s, t):
        return t in self.digraphe[s]

    
    def nb_arêtes(self):
        return sum(len(self.digraphe[s]) for s in self.digraphe.nodes)


    def coords_of_nœud(self, n):
        """ Renvoie le couple (lat, lon)
        Au fait, attention : dans osm l’ordre est inversé : x=lon, y=lat.
        """
        return self.digraphe.nodes[n]["y"], self.digraphe.nodes[n]["x"]

    
    def d_euc(self, n1, n2):
        """ distance euclidienne entre n1 et n2."""
        return distance_euc(self.coords_of_nœud(n1), self.coords_of_nœud(n2))

    
    def parcours_largeur(self, départ, dmax=float("inf")):
        """Itérateur sur les sommets du graphe, selon un parcours en largeur depuis départ. On s’arrête lorsqu’on dépasse la distance dmax depuis départ."""
        àVisiter = deque()
        déjàVu = set({})
        àVisiter.appendleft((départ, 0))
        fini = False
        while len(àVisiter) > 0 and not fini:
            (s, d) = àVisiter.pop()
            if d > dmax: fini = True
            else:
                yield s
                for t in self.digraphe[s].keys():
                    if t not in déjàVu:
                        àVisiter.appendleft((t, d+1))
                        déjàVu.add(t)
