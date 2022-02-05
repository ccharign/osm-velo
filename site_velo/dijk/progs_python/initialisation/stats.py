# -*- coding:utf-8 -*-
"""
 Ce module n’est pas vraiemnt lié à l’appli. Il contient des fonctions de statistiques sur openstreetmap.
"""

import osmnx

def arêtes(g):
    """
    Entrée : g (nx.multidigraph)
    Itérateur sur les arêtes de g
    """
    for s in g.nodes:
        for arêtes in g[s].values():
            for a in arêtes.values():
                yield a


def pourcentage_piéton_et_pistes_cyclables(ville, bavard=0):
    """
    Pourcentage de ways marqués « pedestrian » et « cycleway »
    """
    print("Récupération du graphe")
    g = osmnx.graph_from_place(ville)
    l_piéton, l_pc, l_tot = 0., 0., 0.

    print("Lecture des arêtes")
    for a in arêtes(g):
        longueur = a["length"]
        if "highway" in a:
            l_tot += longueur
            if a["highway"]=="pedestrian":
                l_piéton += longueur
            elif a["highway"] == "cycleway":
                l_pc+=longueur
    return round(l_piéton/l_tot*100, 3), round(l_pc/l_tot*100, 3)
