#!usr/bin/python3
# -*- coding:utf-8 -*-

from importlib import reload  # recharger un module après modif
import networkx as nx  # graphe
from init_graphe import charge_graphe_bbox  # le graphe de Pau par défaut
import apprentissage
import dijkstra
import chemins  # classe chemin et lecture du csv
import utils


g = charge_graphe_bbox()

tous_les_chemins = chemins.chemins_of_csv(g)


def ajoute_chemin(étapes, AR=True, pourcentage_détour=30):
    tous_les_chemins.append(chemins.Chemin.of_étapes(étapes, pourcentage_détour, AR, g))


ajoute_chemin( ["1 rue Louis Barthou", "rue Lamothe", "rue Jean Monnet", "rue Galos", "place de la république"], True, 20)

tous_les_chemins = utils.cheminsValides(tous_les_chemins, g)




def affiche_avant_après(chemins, g, nb_lectures):
    #chemins_avant = [dijkstra.chemin_entre_deux_ensembles(g, c.départ(), c.arrivée(), 0) for c in chemins]
    #g.réinitialise_cyclabilité()
    apprentissage.n_lectures(nb_lectures, g, chemins, bavard=2)

    utils.dessine_chemins(chemins, g)


def test(départ, arrivée, p_détour):
    """ départ et arrivée : des adresses (type str)"""
    g.réinitialise_cyclabilité()
    id_d = g.nœud_centre_rue(départ)
    id_a = g.nœud_centre_rue(arrivée)

    chemin_avant = g.chemin(id_d, id_a, p_détour)

    apprentissage.n_lectures(10, g, tous_les_chemins, bavard=1)

    chemin_après = g.chemin(id_d, id_a, p_détour)

    g.affiche_chemins([chemin_avant, chemin_après], {"route_colors": ["r","b"]})


#apprentissage.n_lectures(15, g, tous_les_chemins, bavard=1)

# vérif de la structure
for c in tous_les_chemins:
    for é in c.étapes:
        try:
            rien = é.nœuds
        except Exception as e:
            print(e)
            print(c)


for i, c in enumerate(tous_les_chemins):
    print(i, c)
