#!usr/bin/python3
# -*- coding:utf-8 -*-

from importlib import reload  # recharger un module après modif
import networkx as nx  # graphe
import os
os.chdir("progs_python")
from init_graphe import charge_graphe  # le graphe de Pau par défaut
import apprentissage
import dijkstra
import chemins  # classe chemin et lecture du csv
import utils
import initialisation.nœuds_des_rues as nr
import lecture_adresse.arbresLex as lex
g = charge_graphe(bavard=2)
#nr.sortie_csv(g)



tous_les_chemins = chemins.chemins_of_csv(g, bavard=1)
len(tous_les_chemins)


def ajoute_chemin(étapes, AR=True, pourcentage_détour=30):
    c = Chemin.of_étapes(étapes, pourcentage_détour, AR, g)
    utils.dessine_chemin(c,g)
    confirme = input("Est-ce-que le chemin est correct ? (O/n)")
    if confirme in ["","o","O"]:
        tous_les_chemins.append(c)
    
    


ajoute_chemin( ["lycée Louis Barthou", "rue Lamothe", "rue Jean Monnet", "rue Galos", "place de la république"], True, 20)
ajoute_chemin(["rue des véroniques", "rue sambre et meuse", "avenue bié-moulié","avenue des acacias", "boulevard barbanègre"], True, 30)

tous_les_chemins = utils.cheminsValides(tous_les_chemins, g)
len(tous_les_chemins)



def affiche_texte_chemins(chemins=tous_les_chemins):
    for i,c in enumerate(chemins):
        print(f"{i} : {c}\n")


    
def affiche_séparément(chemins=tous_les_chemins, g=g):
    for i, c in enumerate(chemins):
        print(f"{i} : {c}")
        utils.dessine_chemin(c, g)
    

apprentissage.n_lectures(10, g, tous_les_chemins, bavard=1)

affiche_séparément()

# vérif de la structure
for c in tous_les_chemins:
    for é in c.étapes:
        try:
            rien = é.nœuds
        except Exception as e:
            print(e)
            print(c)



