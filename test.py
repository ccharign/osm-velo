# -*- coding:utf-8 -*-

from importlib import reload # recharger un module après modif

import networkx as nx # graphe
import osmnx as ox
import requests
import matplotlib.cm as cm
import matplotlib.colors as colors
ox.config(use_cache=True, log_console=True)


from module_graphe import graphe #ma classe de graphe
from init_graphe import g # le graphe de Pau par défaut
#import récup_données as rd
import apprentissage
import dijkstra

import chemins # classe chemin et lecture du csv




tous_les_chemins = chemins.chemins_of_csv(g)


def ajoute_chemin(étapes, AR=True, pourcentage_détour=30):
    tous_les_chemins.append(chemins.Chemin.of_étapes(étapes, pourcentage_détour, AR, g))

ajoute_chemin( ["1 rue Louis Barthou", "rue Lamothe", "rue Jean Monnet", "rue Galos", "place de la république"], True, 20)


def dessine_chemins(chemins, g):

    chemins_directs=[]
    for c in chemins:
        try:
            chemins_directs.append( dijkstra.chemin(g, c.départ(), c.arrivée(), c.p_détour))
        except dijkstra.PasDeChemin:
            print(f"Pas de chemin pour {c}")

    chemins_complets=[]
    for c in chemins:
        try:
            chemins_complets.append( dijkstra.chemin_étapes(g, c) )
        except dijkstra.PasDeChemin as e :
            print(e)
            print(f"Pas de chemin avec étapes pour {c}")
            
    #chemins_complets = [ dijkstra.chemin_étapes(g, c) for c in chemins ]
    g.affiche_chemins(chemins_directs+chemins_complets )


def cheminsValides(chemins):
    """ Renvoie les chemins pour lesquels dijkstra.chemin_étapes a fonctionné sans erreur."""
    res=[]
    for c in chemins:
        try:
            dijkstra.chemin_étapes(g, c)
            res.append(c)
        except dijkstra.PasDeChemin as e :
            print(e)
            print(f"Pas de chemin avec étapes pour {c}")
    return res
tous_les_chemins = cheminsValides(tous_les_chemins)
    
def affiche_chemins(chemins):
    for c in chemins:
        print(c)
        print(c.étapes)

        
def affiche_avant_après(chemins, g, nb_lectures):
    
    chemins_avant = [ dijkstra.chemin(g, c.départ(), c.arrivée(), 0) for c in chemins ]
    #g.réinitialise_cyclabilité()
    for _ in range(nb_lectures):
        apprentissage.lecture_plusieurs_chemins(g, chemins, bavard=1)
    
    chemins_après = [ dijkstra.chemin(g, c.départ(), c.arrivée(), c.p_détour) for c in chemins ]
    
    g.affiche_chemins( chemins_avant+chemins_après, {"route_colors":['r']*len(chemins_avant)+['b']*len(chemins_après)} )


def test(départ, arrivée, p_détour):
    """ départ et arrivée : des adresses (type str)"""
    g.réinitialise_cyclabilité()
    id_d = g.nœud_centre_rue(départ)
    id_a = g.nœud_centre_rue(arrivée)

    chemin_avant = g.chemin(id_d, id_a, p_détour)


    apprentissage.n_lectures(10, g, tous_les_chemins, bavard=1)

    chemin_après = g.chemin(id_d, id_a, p_détour)

    g.affiche_chemins([chemin_avant, chemin_après], {"route_colors":["r","b"]})

#test("rue Jules Supervielle", "cours Bosquet", 0.3)
#"avenue des marronniers", "boulevard Barbanègre"

apprentissage.n_lectures(15, g, tous_les_chemins, bavard=1)

def itinéraire(départ, arrivée, p_détour, g):
    """ Fonction finale. Affiche l'itinéraire, en utilisant le graphe déjà entrainé."""
    id_d = g.nœud_centre_rue(départ)
    id_a = g.nœud_centre_rue(arrivée)
    c = g.chemin(id_d, id_a, p_détour)
    g.affiche_chemin(c)

def test_folium(départ, arrivée, p_détour, où_enregistrer="tmp", g=g):
    id_d = g.nœud_centre_rue(départ)
    id_a = g.nœud_centre_rue(arrivée)
    c = g.chemin(id_d, id_a, p_détour)
    graphe_c = g.multidigraphe.subgraph(c)
    carte = ox.plot_graph_folium(graphe_c, popup_attribute="name")
    nom = os.path.join(où_enregistrer, départ+arrivée+".html")
    carte.save(nom)
    #ox.plot_route_folium(g.multidigraphe,c)
