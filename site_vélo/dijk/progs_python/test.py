#!usr/bin/python3
# -*- coding:utf-8 -*-


## Peut être exécuté directement hors de Django


from importlib import reload  # recharger un module après modif
import networkx as nx  # graphe
import os
os.chdir("site_vélo/") # Depuis emacs je suis dans le dossier osm-vélo, celui qui contient le .git
import dijk.progs_python.params
from init_graphe import charge_graphe  # le graphe de Pau par défaut
import apprentissage
import dijkstra
import chemins  # classe chemin et lecture du csvimport utils
#import initialisation.nœuds_des_rues as nr
#import lecture_adresse.arbresLex as lex
from lecture_adresse.normalisation import normalise_rue, VILLE_DÉFAUT
import utils
import petites_fonctions
g = charge_graphe(bavard=2)
#nr.sortie_csv(g)



arêtes_barbanègre= chemins.arêtes_interdites(g, ["boulevard barbanègre"])
c = chemins.Chemin([chemins.Étape("rue des véroniques", g), chemins.Étape("place royale", g) ], .4, False, interdites=arêtes_barbanègre)
iti, l_ressentie = dijkstra.chemin_étapes_ensembles(g, c, bavard=3)


iti_place_oryale=[459812758, 2627270726, 1724490302, 459642296, 459807936, 459642295, 459807929, 459807931, 459807928, 247979972, 459278230, 459278232, 459278234, 766490866, 459278246, 459278239, 5851108193, 459278271, 459278256, 459278227, 459278251, 459278255, 460007224, 8449237199, 459278225, 2926405952, 459278224, 459278316, 459278217, 459278302, 286693842, 286693848, 286693850, 7080130615, 7080130616, 7080130617, 7080130619, 7080130625, 7080130628, 7080130626, 459161255, 360814074, 2892021617, 2892021615, 8767369241, 9018222917, 9018165416, 360843281, 2990506693, 6384429195, 6384429197, 360814208, 360814205, 360814196, 360814192, 360814173, 360814168, 7016742266, 8463614955, 360814136, 3478438688, 360814125, 286777485, 286777483, 2990664960, 2635148675, 1436423910, 339465315, 286678874, 286678873, 343522520, 286830449, 345532657, 286830447, 5891286604, 5891286600, 6126276486, 307639927, 307639926, 307639922, 307639921, 353108419, 353108417, 252152613, 252152612, 5485497987, 307612550, 307360934]
for s,t in  petites_fonctions.deuxConséc(iti):
    if s in c.interdites and t in c.interdites[s]:
        print(s,t)

list(g.voisins(286678873,.4, interdites = c.interdites))

        
tous_les_chemins = chemins.chemins_of_csv(g, bavard=1)
len(tous_les_chemins)


def ajoute_chemin(étapes, AR=True, pourcentage_détour=30):
    c = chemins.Chemin.of_étapes(étapes, pourcentage_détour, AR, g)
    utils.dessine_chemin(c, g, ouvrir=True)
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
    

apprentissage.n_lectures(5, g, tous_les_chemins, bavard=0)

affiche_séparément()

# vérif de la structure
for c in tous_les_chemins:
    for é in c.étapes:
        try:
            rien = é.nœuds
        except Exception as e:
            print(e)
            print(c)



