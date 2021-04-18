# -*- coding:utf-8 -*-

from importlib import reload # recharger un module après modif

import networkx as nx # graphe
import osmnx as ox
import requests
import matplotlib.cm as cm
import matplotlib.colors as colors
ox.config(use_cache=True, log_console=True, all_oneway=False)
#import overpy #interface Python pour overpass


from module_graphe import graphe #ma classe de graphe
import init_graphe
#import récup_données as rd
import apprentissage
import dijkstra

import chemins # classe chemin et lecture du csv

g = init_graphe.charge_graphe(bavard=1)


tous_les_chemins = chemins.chemins_of_csv("données/chemins.csv", g)

def ajoute_chemin(étapes, AR=True, pourcentage_détour=30):
    tous_les_chemins.append(chemins.Chemin.of_étapes(étapes, pourcentage_détour, AR, g))

ajoute_chemin( ["rue Louis Barthou", "rue Lamothe", "rue Jean Monnet", "rue Galos", "place de la république"], True, 20)

def affiche_chemins(chemins, g):
    chemins_complets = [ dijkstra.chemin_étapes(g, c) for c in chemins ]
    g.affiche_chemins(chemins_complets)

    
def affiche_avant_après(chemins, g, nb_lectures):
    
    chemins_avant = [ dijkstra.chemin(g, c.départ(), c.arrivée(), c.p_détour) for c in chemins ]
    g.réinitialise_cyclabilité()
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

apprentissage.n_lectures(10, g, tous_les_chemins, bavard=1)

def itinéraire(départ, arrivée, p_détour, g):
    """ Fonction finale. Affiche l'itinéraire, en utilisant le graphe déjà entrainé."""
    id_d = g.nœud_centre_rue(départ)
    id_a = g.nœud_centre_rue(arrivée)
    c = g.chemin(id_d, id_a, p_détour)
    g.affiche_chemin(c)
