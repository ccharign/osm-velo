# -*- coding:utf-8 -*-

### Fonctions diverses pour utiliser le logiciel


from importlib import reload  # recharger un module après modif
import subprocess
import networkx as nx  # graphe
import osmnx as ox
ox.config(use_cache=True, log_console=True)
from module_graphe import graphe  #ma classe de graphe
#import récup_données as rd
import apprentissage
import dijkstra
import chemins  # classe chemin et lecture du csv
from params import VILLE_DÉFAUT, NAVIGATEUR
import os
import récup_données
import module_graphe


def ouvre_html(chemin):
    res = subprocess.run([NAVIGATEUR, chemin], capture_output=True)


def cheminsValides(chemins, g):
    """ Renvoie les chemins pour lesquels dijkstra.chemin_étapes a fonctionné sans erreur."""
    res = []
    for c in chemins:
        try:
            dijkstra.chemin_étapes_ensembles(g, c)
            res.append(c)
        except dijkstra.PasDeChemin as e:
            print(e)
            print(f"Pas de chemin avec étapes pour {c}")
    return res


def itinéraire(départ, arrivée, p_détour, g, où_enregistrer="tmp", bavard=0):
    d = chemins.Étape(départ, g)
    a = chemins.Étape(arrivée, g)
    c = chemins.Chemin([d, a], p_détour, False)
    res = g.chemin_étapes_ensembles(c)
    graphe_c = g.multidigraphe.subgraph(res)
    carte = ox.plot_graph_folium(graphe_c, popup_attribute="name")
    nom = os.path.join(où_enregistrer, départ+arrivée+".html")
    carte.save(nom)
    ouvre_html(nom)
    #ox.plot_route_folium(g.multidigraphe,c)


    
#################### Affichage ####################



# Affichage folium avec couleur
# voir https://stackoverflow.com/questions/56234047/osmnx-plot-a-network-on-an-interactive-web-map-with-different-colours-per-infra


def flatten(c):
    res = []
    for x in c:
        res.extend(x)
    return res


def dessine_chemins(chemins, g, où_enregistrer="tmp"):

    chemins_directs = []
    for c in chemins:
        try:
            chemins_directs.append(c.chemin_direct_sans_cycla(g))
        except dijkstra.PasDeChemin:
            print(f"Pas de chemin pour {c}")
    graphe_c_directs = g.multidigraphe.subgraph(flatten(chemins_directs))
    carte = ox.plot_graph_folium(graphe_c_directs, popup_attribute="name", color="red")

    chemins_complets = []
    for c in chemins:
        try:
            chemins_complets.append(dijkstra.chemin_étapes_ensembles(g, c))
        except dijkstra.PasDeChemin as e:
            print(e)
            print(f"Pas de chemin avec étapes pour {c}")
    graphe_c_complet = g.multidigraphe.subgraph(flatten(chemins_complets))
    carte = ox.plot_graph_folium(graphe_c_complet, popup_attribute="name", color="blue", graph_map=carte)  # On rajoute ce graphe par-dessus le précédent dans le folium
    
    nom = os.path.join(où_enregistrer, "dessine_chemins.html")
    carte.save(nom)
    ouvre_html(nom)


def affiche_sommets(s, g, où_enregistrer="tmp"):
    """ Entrée : s, liste de sommets """
    graphe_c = g.multidigraphe.subgraph(s)
    carte = ox.plot_graph_folium(graphe_c, popup_attribute="name")
    nom = os.path.join(où_enregistrer, "affiche_sommets.html")
    carte.save(nom)
    subprocess.run([NAVIGATEUR, nom])


def affiche_rue(ville, rue, g, bavard=0):
    """
    Entrées : g, graphe
              
    """
    #sommets = chemins.nœud_of_étape(adresse, g, bavard=bavard-1)
    sommets = g.nœuds[str(ville)][rue]
    affiche_sommets(sommets, g)
