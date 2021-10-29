# -*- coding:utf-8 -*-

### Fichier destiné à être chargé à chaque utilisation ###


#import networkx as nx
from params import RACINE_PROJET, DONNÉES, BBOX_DÉFAUT
from module_graphe import graphe  # ma classe de graphe

from initialisation.ajoute_villes import ajoute_villes
import initialisation.noeuds_des_rues as nr

import time
#import osmnx.io
from networkx import read_graphml
import subprocess
import os
#ox.config(use_cache=True, log_console=True)




# Pour la simplification dans osmnx :
# https://github.com/gboeing/osmnx-examples/blob/master/notebooks/04-simplify-graph-consolidate-nodes.ipynb

# filtrage
# https://stackoverflow.com/questions/63466207/how-to-create-a-filtered-graph-from-an-osm-formatted-xml-file-using-osmnx


#################### Récupération du graphe via osmnx ####################


def charge_graphe(bbox=BBOX_DÉFAUT, option={"network_type":"all"}, bavard=1):
    """
    Renvoie le graphe (instance de graphe) correspondant à la bbox indiquée.
    """
    
    s,o,n,e = bbox 
    nom_fichier = f'{DONNÉES}/{s}{o}{n}{e}.graphml'
    if bavard>0:print(bbox, nom_fichier)
    if os.path.exists(nom_fichier):
        #g = osmnx.io.load_graphml(nom_fichier)
        g = read_graphml(nom_fichier)
        if bavard>0: print("Graphe en mémoire !")
    else:
        print(f"\nGraphe pas en mémoire à {nom_fichier}, je le charge via osmnx.\\")

        à_exécuter = [
            os.path.join(RACINE_PROJET, "progs_python/initialisation/crée_graphe.py".encode("utf-8")),
            nom_fichier,
            str(bbox)
        ]
        if bavard>0:print(à_exécuter)
        sortie = subprocess.run(à_exécuter)
        if bavard>1:print(sortie.stdout)
        print(sortie.stderr)
        #g = osmnx.io.load_graphml(nom_fichier)
        g = read_graphml(nom_fichier)
        
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









