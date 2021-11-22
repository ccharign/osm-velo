# -*- coding:utf-8 -*-

import networkx as nx
from petites_fonctions import distance_euc



class Graphe_minimaliste():
    """
    Classe de graphe avec uniquement le graphe networkx tiré d’osm.
    Pour être utilisé lors de la phase d’initialisation quamd aucune donnée n’a encore été obtenue.
    Munie tout de même des méthodes rue_dune_arête et ville_dune_sommet. Le première fonctionne grâce au champ « name » présent dans les arêtes dans le grphe renvoyé par osm. La seconde grâce au dico ville_of_nœud, rempli par ajoute_villes.

    Attributs:
        multidigraphe
        digraphe
        villes_of_nœud : dictionnaire nœud -> liste des villes
    """
    
    def __init__(self, g):
        """ Entrée : g, MultiDiGraph de networkx"""
        self.multidigraphe = g
        print("Calcul de la version sans multiarêtes")
        self.digraphe = nx.DiGraph(g)  # ox.get_digraph(g)
        self.villes_of_nœud={}


    def __contains__(self, n):
        """ Indique si le nœud n est dans g"""
        return n in self.digraphe.nodes
    
    def voisins_nus(self, s):
        """ Itérateur sur les voisins de s, sans la longueur de l’arête."""
        return self.digraphe[s].keys()

    
    def est_arête(self, s, t):
        return t in self.digraphe[s]

    
    def nb_arêtes(self):
        return sum(len(self.digraphe[s]) for s in self.digraphe.nodes)


    def coords_of_nœud(self, n):
        """ Renvoie le couple (lon, lat)
         dans osmnx : x=lon, y=lat.
        """
        return self.digraphe.nodes[n]["x"], self.digraphe.nodes[n]["y"]

    
    def d_euc(self, n1, n2):
        """ distance euclidienne entre n1 et n2."""
        return distance_euc(self.coords_of_nœud(n1), self.coords_of_nœud(n2))

    
    def rue_dune_arête(self, s, t, bavard=0):
        """ Tuple des noms des rues contenant l’arête (s,t). Le plus souvent un singleton.
            Renvoie None si celui-ci n’est pas présent (pas de champ "name" dans les données de l’arête)."""
        try:
            res = self.digraphe[s][t]["name"]
            if isinstance(res, str):
                return res,
            else:
                return res
        except KeyError:
            if bavard>0:
                print(f"L’arête {(s,t)} n’a pas de nom. Voici ses données\n {self.digraphe[s][t]}")

    def ville_dune_arête(self, s, t, bavard=0):
        """ Liste des villes contenant l’arête (s,t).
        """
        try:
            return self.digraphe[s][t]["ville"] 
        except KeyError:
            if bavard>0: print(f"Pas de ville en mémoire pour l’arête {s,t}.  Voici ses données\n {self.digraphe[s][t]}")
            return []

    def villes_dun_sommet(self, s):
        """
        Entrée : s (int), sommet du graphe.
        Sortie : liste des villes de ce sommet.
        """
        try:
            return self.villes_of_nœud[s]
        except KeyError:
            if bavard>0: print(f"Pas de ville en mémoire pour l’arête {s,t}.  Voici ses données\n {self.digraphe[s][t]}")
            return []

    def nb_arêtes_avec_ville(self):
        return sum(
            len([t for t in self.digraphe[s] if "ville" in self.digraphe[s][t]])
            for s in self.digraphe.nodes 
        )
    
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

    def vers_csv(self, chemin):
        """
        Crée un csv avec la liste des arêtes et leurs longueurs.
        """
        with open(chemin,"w") as sortie:
            for s in self.digraphe.nodes:
                for t, données in self.digraphe[s].items():
                    sortie.write(f"{s},{t},{données['length']}\n")
