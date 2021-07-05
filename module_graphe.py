# -*- coding:utf-8 -*-

import networkx as nx
from osmnx import plot_graph, get_nearest_node
import os
import dijkstra
from récup_données import coords_lieu, cherche_lieu, nœuds_sur_tronçon_local
from params import VILLE_DÉFAUT, LOG_PB
from petites_fonctions import distance_euc


class PasTrouvé(Exception):
    pass


class graphe():
    """
    Attributs : - multidigraphe : un multidigraph de networkx
                - digraphe : le digraph correspondant
                - cyclabilité un dictionnaire (int * int) -> float, qui associe à une arrête (couple des id osm des nœuds) sa cyclabilité. Valeur par défaut : 1. Les distances serot divisées par  (p_détour × cycla + 1 - p_détour).
                - nœud_of_rue : dictionnaire de type str -> int qui associe à un nom de rue l'identifiant correspondant dans le graphe. Calculé au moyen de la méthode un_nœud_sur_rue. Sert de cache. La clé utilisée est "nom_rue,ville,pays".
    """
   
    def __init__(self, g):
        """ g, MultiDiGraph"""
        self.multidigraphe = g
        print("Calcul de la version sans multiarêtes")
        self.digraphe = nx.DiGraph(g)  # ox.get_digraph(g)
        self.cyclabilité = {}
        self.nœud_of_rue = {}
       
    def voisins(self, s, p_détour):
        """
        La méthode utilisée par dijkstra.
        Renvoie les couples (voisin, longueur de l'arrête) issus du sommet s.
        p_détour (float) : pourcentage de détour accepté.
        La longueur de l'arrête (s,t) est sa longueur physique divisée par sa cyclabilité (s'il y en a une).
        """
        cycla_corrigée = lambda voisin: (p_détour * self.cyclabilité.get((s, voisin), 1.) + 1 - p_détour)
        return ( ( voisin, données["length"]/cycla_corrigée(voisin) )  for (voisin, données) in self.digraphe[s].items() )
   
    def liste_voisins(self, s):
        return list(self.voisins)
   
    def est_arrête(self, s, t):
        return t in self.digraphe[s]
  
    def chemin(self, d, a, p_détour):
        return dijkstra.chemin(self, d, a, p_détour)
  
    def chemin_étapes_ensembles(self, c):
        """ Entrée : c, objet de la classe Chemin"""
        return dijkstra.chemin_étapes_ensembles(self, c)

    def affiche(self):
        plot_graph(self.multidigraphe, node_size=10)

         
    def nœud_le_plus_proche(self, coords):
        return get_nearest_node(self.multidigraphe, coords)
 
    def nœud_centre_rue(self, nom_rue, ville=VILLE_DÉFAUT, pays="France"):
        """ Renvoie le nœud le plus proche des coords enregistrées dans osm pour la rue.
        Pb si trop de nœuds ont été supprimés par osmnx ? """
        coords = coords_lieu(nom_rue, ville=ville, pays="France")
        return self.nœud_le_plus_proche(coords)

    def un_nœud_sur_rue(self, nom_rue,  ville=VILLE_DÉFAUT, pays="France"):
        """ Renvoie un nœud OSM de la rue, qui soit présent dans le graphe. Renvoie le nœud médian parmi ceux présents.
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
       
    def sauv_cache(self, chemin="données"):
        """ chemin est le chemin du répertoire. Le nom du fichier sera  "nœud_of_rue.csv"."""
        adresse = os.path.join(chemin, "nœud_of_rue.csv")
        sortie = open(adresse, "w")
        
        for c, v in self.nœud_of_rue.items():
            à_écrire = ",".join(map(str, v))
            sortie.write(f"{c}:{à_écrire}\n")
        sortie.close()

    def charge_cache(self, chemin="données"):
        print("Chargement du cache nœud_of_rue.""")
        adresse = os.path.join(chemin, "nœud_of_rue.csv")
        entrée = open(adresse)
        for ligne in entrée:
            c, v = ligne.strip().split(":")
            l = list(map(int, v.split(",")))
            self.nœud_of_rue[c] = l
        entrée.close()

    def vide_cache(self, chemin="données"):
        adresse = os.path.join(chemin, "nœud_of_rue.csv")
        entrée = open(adresse, "w")
        entrée.close()
       
    def sauv_cycla(self, chemin="données/"):
        """ chemin : adresse et nom du fichier, sans l'extension"""
        sortie = open(os.path.join(chemin, "Cyclabilité.csv"), "w")
        for (s, t), v in self.cyclabilité.items():
            sortie.write(f"{s};{t};{v}\n")
        sortie.close()

    def charge_cycla(self, chemin="données/"):
        entrée = open(os.path.join(chemin, "Cyclabilité.csv"))
        for ligne in entrée:
            s, t, v = ligne.strip().split(";")
            self.cyclabilité[(s, t)] = v
        entrée.close()


def nœuds_rue_of_arête(g, s, t):
    """Entrée : g (digraph)
                s, t : deux sommets adjacents
       Sortie : liste des nœuds de la rue contenant l’arête (s, t). La rue est identifiée par le paramètre "name" dans le graphe."""

    déjàVu = {}  # En cas d’une rue qui bouclerait...
    nom = g[s][t]["name"]
    
    def nœud_dans_direction(g, s, t, res):
        """ Mêmes entrées, ainsi que res, tableau où mettre le résultat.
        t sera mis dans res et noté déjÀVu, mais pas s.

        Renvoie les nœuds uniquement dans la direction (s,t), càd ceux auxquels on accède via t et non via s."""

        res.append(t)
        déjàVu[t] = True
        voisins = [v for v in g[t] if v not in déjàVu and v!=s and g[t][v].get("name", "") == nom]
        if len(voisins) == 0:
            return res
        elif len(voisins) == 1:
            return nœud_dans_direction(g, t, voisins[0], res)
        else:
            print(f"Trop de voisins pour le nœud {t} dans la rue {nom}.")
            return nœud_dans_direction(g, t, voisins[0], res)
       
    return list(reversed(nœud_dans_direction(g, s, t, []))) + nœud_dans_direction(g, t, s, [])


def nœuds_rue_of_nom_et_nœud(g, n, nom):
    """ Entrée : n (int) un nœud de la rue
                 nom (str) le nom de la rue. Doit être le nom exact utilisé par osm et reporté dans le graphe.
        Sortie : liste des nœuds de la rue, dans l’ordre topologique."""

    for v in g[n]:
        if g[n][v].get("name", "") == nom:
            return nœuds_rue_of_arête(g, n, v)
    raise PasTrouvé(f"Pas trouvé de voisin pour le nœud {n} dans la rue {nom}")


def nœuds_sur_rue(g, nom_rue, ville=VILLE_DÉFAUT, pays="France", bavard=1):
    """ Entrée : g (digraph)
                 nom_rue (str)
        Sortie : liste des nœuds de cette rue, dans l’ordre topologique."""

    lieu = cherche_lieu(nom_rue, ville=ville, pays=pays, bavard=bavard-1)

    for tronçon in lieu:
        if tronçon.raw["osm_type"] == "way":
            nom = lieu[0].raw["display_name"].split(",")[0]  # est-ce bien fiable ?
            print(f"nom trouvé : {nom}")
            id_rue = tronçon.raw["osm_id"]
            nœuds = nœuds_sur_tronçon_local(id_rue)
            for n in nœuds:
                if n in g.nodes:
                    return nœuds_rue_of_nom_et_nœud(g, n, nom)
    raise PasTrouvé(f"Pas réussi à trouver la rue et un nœud dessus : {nom_rue} ({ville})")


def nœud_sur_rue_le_plus_proche(g, coords, nom_rue, ville=VILLE_DÉFAUT, pays="France", bavard=0):
    """ 
    Entrée : g (digraph)
             nom_rue (str)
             coords ( (float, float) )
    Renvoie le nœud sur la rue nom_rue le plus proche de coords."""

    def coords_of_nœud(n):
        return g.nodes[n]["x"], g.nodes[n]["y"]
    nœuds = nœuds_sur_rue(g, nom_rue, ville=ville, pays=pays, bavard=bavard-1)
    tab = [ (distance_euc(coords_of_nœud(n),coords), n) for n in nœuds ]
    _, res = min(tab)
    return res
