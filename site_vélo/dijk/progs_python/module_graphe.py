# -*- coding:utf-8 -*-

import networkx as nx
from osmnx import plot_graph, nearest_nodes
import os

from params import LOG_PB, D_MAX_POUR_NŒUD_LE_PLUS_PROCHE, CHEMIN_CACHE, CHEMIN_CYCLA
import dijkstra
from récup_données import coords_lieu, cherche_lieu, nœuds_sur_tronçon_local
from lecture_adresse.normalisation import VILLE_DÉFAUT, normalise_rue
from petites_fonctions import distance_euc, deuxConséc
from collections import deque
from lecture_adresse.récup_nœuds import tous_les_nœuds

class PasTrouvé(Exception):
    pass

class TropLoin(Exception):
    """ Pour le cas où le nœud de g trouvé serait trop loin de l’emplacement initialement recherché."""
    pass


class graphe():
    """
    Attributs : - multidigraphe : un multidigraph de networkx
                - digraphe : le digraph correspondant
                - cyclabilité un dictionnaire (int * int) -> float, qui associe à une arrête (couple des id osm des nœuds) sa cyclabilité. Valeur par défaut : 1. Les distances seront divisées par  (p_détour × cycla + 1 - p_détour).
                - nœud_of_rue : dictionnaire de type str -> int qui associe à un nom de rue l'identifiant correspondant dans le graphe. Calculé au moyen de la méthode un_nœud_sur_rue. Sert de cache. La clé utilisée est "nom_rue,ville,pays".
                - nœuds : dictionnaire ville -> rue -> nœuds. Calculé par un parcours de tous le graphe dans initialisation/nœuds_des_rue.py
    """
   
    def __init__(self, g):
        """ g, MultiDiGraph"""
        self.multidigraphe = g
        print("Calcul de la version sans multiarêtes")
        self.digraphe = nx.DiGraph(g)  # ox.get_digraph(g)
        self.cyclabilité = {}
        self.nœud_of_rue = {}
        self.nœuds = {}

        
    def __contains__(self, n):
        """ Indique si le nœud n est dans g"""
        return n in self.digraphe.nodes

    
    def voisins(self, s, p_détour):
        """
        La méthode utilisée par dijkstra.
        Renvoie les couples (voisin, longueur de l'arrête) issus du sommet s.
        p_détour (float) : pourcentage de détour accepté.
        La longueur de l'arrête (s,t) est sa longueur physique divisée par sa cyclabilité (s'il y en a une).
        """
        #assert s in self.digraphe.nodes, f"le sommet {s} reçu par la méthode voisins n’est pas dans le graphe"
        cycla_corrigée = lambda voisin: (p_détour * self.cyclabilité.get((s, voisin), 1.) + 1 - p_détour)
        return ( ( voisin, données["length"]/cycla_corrigée(voisin) )  for (voisin, données) in self.digraphe[s].items() )

    def voisins_nus(self, s):
        """ Itérateur sur les voisins de s, sans la longueur de l’arête."""
        return (t for t in self.digraphe[s].keys())

    def longueur_itinéraire(self, iti):
        """
        Entrée : un itinéraire (liste de sommets)
        Sortie : sa « vraie » longueur.
        """
        return int(sum(self.longueur_arête(s,t) for s,t in deuxConséc(iti)))
        
    
    def liste_voisins(self, s):
        return list(self.voisins)
   
    def est_arête(self, s, t):
        return t in self.digraphe[s]

    def longueur_arête(self, s, t):
        return self.digraphe[s][t]["length"]

    def nb_arêtes(self):
        return sum(len(self.digraphe[s]) for s in self.digraphe.nodes)

    def nb_arêtes_avec_ville(self):
        return sum(
            len([t for t in self.digraphe[s] if "ville" in self.digraphe[s][t]])
            for s in self.digraphe.nodes 
        )

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

    
    def chemin(self, d, a, p_détour):
        return dijkstra.chemin(self, d, a, p_détour)
  
    def chemin_étapes_ensembles(self, c, bavard=0):
        """ Entrée : c, objet de la classe Chemin"""
        return dijkstra.chemin_étapes_ensembles(self, c, bavard=bavard)

    def affiche(self):
        plot_graph(self.multidigraphe, node_size=10)

         
    def nœud_le_plus_proche(self, coords, recherche = "", d_max = D_MAX_POUR_NŒUD_LE_PLUS_PROCHE ):
        """
        recherche est la recherche initiale qui a eu besoin de cet appel. Uniquement pour compléter l’erreur qui sera levée si le nœud le plus proche est à distance > d_max.
        Les coords doivent être dans l’ordre (lon, lat).
        """
        
        n, d = nearest_nodes(self.multidigraphe, *coords, return_dist = True)
        if d > d_max:
            print(f" Distance entre {self.coords_of_nœud(n)} et {coords} supérieure à {d_max}.")
            raise TropLoin(recherche)
        else:
            return n
 
    def nœud_centre_rue(self, nom_rue, ville=VILLE_DÉFAUT, pays="France"):
        """ Renvoie le nœud le plus proche des coords enregistrées dans osm pour la rue.
        Pb si trop de nœuds ont été supprimés par osmnx ? """
        coords = coords_lieu(nom_rue, ville=ville, pays="France")
        return self.nœud_le_plus_proche(coords)

    def un_nœud_sur_rue(self, nom_rue,  ville=VILLE_DÉFAUT, pays="France"):
        """
        OBSOLÈTE
        Renvoie un nœud OSM de la rue, qui soit présent dans le graphe. Renvoie le nœud médian parmi ceux présents.
        Si échec, renvoie un nœud le plus proche de la coordonnée associé à la rue par Nominatim."""
        raise RuntimeError("Cette fonction n’est plus censée être utilisée")
        nom_rue = nom_rue.strip()
        ville = ville.strip()
        pays = pays.strip()
        clef = f"{nom_rue},{ville},{pays}"
     
        def renvoie(res):
            self.nœud_of_rue[clef] = res
            print(f"Mis en cache : {res} pour {clef}")
            return res
     
        if clef in self.nœud_of_rue:  # Recherche dans le cache
            return self.nœud_of_rue[clef]
        else:
            #try:
                print(f"Recherche d'un nœud pour {nom_rue}")
                nœuds = nœuds_rue_of_adresse(self.digraphe, nom_rue, ville=ville, pays=pays)
                n = len(nœuds)
                if n > 0:
                    return renvoie(nœuds[n//2])
                else:
                    print(f"Pas trouvé de nœud exactement sur {nom_rue} ({ville}). Je recherche le nœud le plus proche.")
                    return renvoie(self.nœud_centre_rue(nom_rue, ville=ville, pays=pays))
            #except Exception as e:
            #    print(f"Erreur lors de la recherche d'un nœud sur la rue {nom_rue} : {e}")

               

    
    def coords_of_nœud(self, n):
        """ Renvoie le couple (lat, lon)
        Au fait, attention : dans osm l’ordre est inversé : x=lon, y=lat.
        """
        return self.digraphe.nodes[n]["y"], self.digraphe.nodes[n]["x"]

       
               
    def incr_cyclabilité(self, a, dc):
        """ Augmente la cyclabilité de l'arête a (couple de nœuds), ou l'initialise si elle n'était pas encore définie.
        Formule appliquée : *= (1+dc)
        """
        assert dc > -1, "Reçu un dc <= -1 "
        if a in self.cyclabilité: self.cyclabilité[a] *= (1+dc)
        else: self.cyclabilité[a] = 1. + dc

    def réinitialise_cyclabilité(self):
        self.cyclabilité = {}

    
    def rue_of_nœud(self, n):
        """ renvoie le nom de la rue associée dans le cache au nœud n"""
        for c, v in self.nœud_of_rue.items():
            if n in v:
                return c
        raise KeyError("Le nœud {n} n'est pas dans le cache")
       
    def sauv_cache(self):
        """ L’adresse du fichier csv est dans CHEMIN_CACHE."""
        sortie = open(CHEMIN_CACHE, "w")
        
        for c, v in self.nœud_of_rue.items():
            à_écrire = ",".join(map(str, v))
            sortie.write(f"{c}:{à_écrire}\n")
        sortie.close()

    def charge_cache(self):
        print("Chargement du cache nœud_of_rue.")
        entrée = open(CHEMIN_CACHE)
        for ligne in entrée:
            c, v = ligne.strip().split(":")
            l = list(map(int, v.split(",")))
            self.nœud_of_rue[c] = l
        entrée.close()

    def vide_cache(self):
        print("J’efface le cache des adresses")
        entrée = open(CHEMIN_CACHE, "w")
        entrée.close()
        self.nœud_of_rue={}
       
    def sauv_cycla(self):
        """ chemin : adresse et nom du fichier, sans l'extension"""
        print("Sauvegarde de la cyclabilité")
        sortie = open(CHEMIN_CYCLA, "w")
        for (s, t), v in self.cyclabilité.items():
            sortie.write(f"{s};{t};{v}\n")
        sortie.close()

    def charge_cycla(self):
        """ Charge la  cycla depuis le csv, et enregistre le max en attribut du graphe."""
        print("Chargement de la cyclabilité")
        entrée = open(CHEMIN_CYCLA)
        maxi=0
        for ligne in entrée:
            s, t, v = ligne.strip().split(";")
            s=int(s); t=int(t); v=float(v)
            maxi=max(v, maxi)
            self.cyclabilité[(s, t)] = v
        entrée.close()
        self.cycla_max = maxi
    



def vérif_arêtes(g):
    """ Vérifie que les arêtes de g sont bien des couples de sommets de g."""
    res = []
    for s in g.digraphe.nodes:
        for t in g.voisins_nus(s):
            if t not in g.digraphe.nodes:
                res.append(t)
        for t, _ in g.voisins(s, 0):
            if t not in g.digraphe.nodes:
                res.append(t)
    return res
