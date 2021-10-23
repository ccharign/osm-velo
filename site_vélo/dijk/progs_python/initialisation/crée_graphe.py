#!usr/bin/python3
# -*- coding:utf-8 -*-

### À terme devrait être le seul fichier à utiliser osmnx, afin d’éviter de le charger dans les utilisations courantes.

import osmnx as ox
ox.config(use_cache=True, log_console=True)


D_MAX_SUITE_RUE = 10  # Nombre max d’arêtes où on va chercher pour trouver la suite d’une rue.
BBOX = 43.2671, -0.4285, 43.3403, -0.2541 # Convention overpass : sud, ouest, nord, est



def crée_graphe_bbox(nom_fichier, ouest=-0.4285, sud=43.2671, est=-0.2541, nord=43.3403, option={"network_type":"all"}, bavard=1):
    """ 
    nom_fichier : nom du fichier où enregistrer le fichier xml du graphe.
    Effet : création du fichier graphml
    Sortie : le graphe, au format networkx non dirigé
    """
    
    print(f"Graphe pas en mémoire à {nom_fichier}. Chargement depuis osm.")
    g = ox.graph_from_bbox(nord, sud, est, ouest, **option)
    
    print("conversion en graphe non orienté")
    g = ox.get_undirected(g)
    
    print(f"Chargement fini. Je l'enregistre pour la prochaine fois dans {nom_fichier}.")
    ox.io.save_graphml(g, nom_fichier)
    
    return g


# Choix de la fonction à utiliser. (J'ai supprimé les autres de toute façon!)
charge_graphe = crée_graphe_bbox

# Pour télécharger une carte avec overpass : wget -O pau.osm "https://overpass.openstreetmap.ru/cgi/xapi_meta?*[bbox=-0.4285,43.2671,-0.2541,43.3403]"
#Agglo : wget -O pau.osm "https://overpass.openstreetmap.ru/cgi/xapi_meta?*[bbox=-0.48,43.26,-0.25,43.35]"



if __name__ == "main":
    nom_fichier = subprocess.argv[1]
    charge_graphe_bbox(nom_fichier)


    
