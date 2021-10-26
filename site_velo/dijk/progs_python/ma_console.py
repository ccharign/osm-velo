#!usr/bin/python3 -i
# -*- coding:utf-8 -*-


## Peut être exécuté directement hors de Django pour tests


from importlib import reload  # recharger un module après modif
import os
import params
from init_graphe import charge_graphe  # le graphe de Pau par défaut
import apprentissage
import dijkstra
import chemins  # classe chemin et lecture du csv
#import initialisation.nœuds_des_rues as nr
#import lecture_adresse.arbresLex as lex
from lecture_adresse.normalisation import normalise_rue, VILLE_DÉFAUT
import utils
import petites_fonctions
g = charge_graphe(bavard=3)
