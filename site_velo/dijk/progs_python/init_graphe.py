# -*- coding:utf-8 -*-

### Fichier destiné à être chargé à chaque utilisation ###


#import networkx as nx
from time import perf_counter
from petites_fonctions import chrono
from params import RACINE_PROJET, DONNÉES, BBOX_DÉFAUT
from graphe_par_networkx import Graphe_nw
from module_graphe import Graphe, Graphe_mélange  # ma classe de graphe
from initialisation.ajoute_villes import ajoute_villes
import initialisation.noeuds_des_rues as nr



tic=perf_counter()
from osmnx.io import load_graphml
chrono(tic, "Chargement de osmnx.io.load_graphml (depuis init_graphe)")
#from networkx import read_graphml  # Défaut : ne convertit pas les types des données (longeur, id_osm, coords...), tout reste en str
# https://networkx.org/documentation/stable/reference/readwrite/generated/networkx.readwrite.graphml.read_graphml.html#networkx.readwrite.graphml.read_graphml
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
    Renvoie le graphe (instance de Graphe) correspondant à la bbox indiquée.
    """
    
    s,o,n,e = bbox 
    nom_fichier = f'{DONNÉES}/{s}{o}{n}{e}.graphml'
    if bavard>0:print(f"Nom du fichier du graphe : {nom_fichier}")
    if os.path.exists(nom_fichier):
        tic=perf_counter()
        g = load_graphml(nom_fichier)
        #g = read_graphml(nom_fichier, node_type=int)
        if bavard>0:
            print("Graphe en mémoire !")
            chrono(tic, f"osmnx.io.load_graphml({nom_fichier})")
    else:
        print(f"\nGraphe pas en mémoire à {nom_fichier}, je le charge via osmnx.\\")

        à_exécuter = [
            os.path.join(RACINE_PROJET, "progs_python/initialisation/crée_graphe.py"),
            nom_fichier,
            str(bbox)
        ]
        if bavard>0:print(à_exécuter)
        sortie = subprocess.run(à_exécuter)
        if bavard>1:print(sortie.stdout)
        print(sortie.stderr)
        g = load_graphml(nom_fichier)
        #g = read_graphml(nom_fichier, node_type=int)
        
    gr = Graphe(Graphe_mélange(g))
    
    gr.g.charge_cache()  # nœud_of_rue
    
    print("Chargement de la cyclabilité")
    tic=perf_counter()
    cycla_max=gr.g.charge_cycla()
    gr.cycla_max=cycla_max
    chrono(tic, "ajout de la cycla au graphe")
    

    # print("Ajout du nom des villes")
    # tic=perf_counter()
    # ajoute_villes(gr, bavard=bavard-1)
    # chrono(tic, "ajout du nom des villes au graphe")

    # Plus besoin vu que les rues sont dans la base Django
    # print("Ajout de la liste des nœuds de chaque rue")
    # tic=perf_counter()
    # nr.charge_csv(gr)
    # chrono(tic, "ajout de la liste des nœuds de chaque rue au graphe.")
    
    print("Chargement du graphe fini.\n")
    return gr









