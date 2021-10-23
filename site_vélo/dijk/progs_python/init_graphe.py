# -*- coding:utf-8 -*-

### Fichier destiné à être chargé à chaque utilisation ###


#import networkx as nx
from params import RACINE_PROJET, DONNÉES
from module_graphe import graphe  # ma classe de graphe

from initialisation.ajoute_villes import ajoute_villes
import initialisation.nœuds_des_rues as nr

import time
import osmnx.io
import subprocess
import os
#ox.config(use_cache=True, log_console=True)

BBOX = 43.2671, -0.4285, 43.3403, -0.2541 # Convention overpass : sud, ouest, nord, est


# Pour la simplification dans osmnx :
# https://github.com/gboeing/osmnx-examples/blob/master/notebooks/04-simplify-graph-consolidate-nodes.ipynb

# filtrage
# https://stackoverflow.com/questions/63466207/how-to-create-a-filtered-graph-from-an-osm-formatted-xml-file-using-osmnx


#################### Récupération du graphe via osmnx ####################


def charge_graphe(ouest=-0.4285, sud=43.2671, est=-0.2541, nord=43.3403, option={"network_type":"all"}, bavard=1):
    nom_fichier = f'{DONNÉES}/{ouest}{sud}{est}{nord}.graphml'
    try:
        g = osmnx.io.load_graphml(nom_fichier)
        if bavard: print("Graphe en mémoire !")
    except FileNotFoundError:
        sortie = subprocess.run(["python3", os.path.join(RACINE_PROJET, "initialisation/crée_graphe.py"), nom_fichier], capture_output=True)
        print(sortie.stdout)
        print(sortie.stderr)
        g = osmnx.io.load_graphml(nom_fichier)

    gr = graphe(g)
    gr.charge_cache()  # nœud_of_rue
    
    print("Chargement de la cyclabilité")
    gr.charge_cycla()

    print("Ajout du nom des villes")
    ajoute_villes(gr, bavard=bavard-1)

    print("Ajout de la liste des nœuds de chaque rue")
    nr.charge_csv(gr)
    
    print("Chargement du graphe fini.\n")
    return gr









