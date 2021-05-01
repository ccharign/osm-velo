# -*- coding:utf-8 -*-

import os
import networkx as nx
import osmnx as ox
ox.config(use_cache=True, log_console=True)
from module_graphe import graphe #ma classe de graphe
import xml.etree.ElementTree as xml # Manipuler le xml local

from params import CHEMIN_XML, CHEMIN_XML_COMPLET # Chemin du xml élagué

# Pour la simplification dans osmnx :
# https://github.com/gboeing/osmnx-examples/blob/master/notebooks/04-simplify-graph-consolidate-nodes.ipynb

# filtrage
# https://stackoverflow.com/questions/63466207/how-to-create-a-filtered-graph-from-an-osm-formatted-xml-file-using-osmnx




def charge_graphe_bbox(ouest =-0.4285 , sud=43.2671, est=-0.2541,nord=43.3403, option={"network_type":"all"}, bavard=1):
    nom_fichier = f'données/{ouest}{sud}{est}{nord}.graphml'
    try:
        g= ox.io.load_graphml(nom_fichier)
        if bavard:print("Graphe en mémoire !")
    except FileNotFoundError:
        if bavard:print(f"Graphe pas en mémoire à {nom_fichier}. Chargement depuis osm.")
        g=ox.graph_from_bbox(nord, sud, est, ouest, **option)
        print("conversion en graphe non orienté")
        g=ox.get_undirected(g)
        if bavard:print("Chargement fini. Je l'enregistre pour la prochaine fois.")
        ox.io.save_graphml(g, nom_fichier)


    gr = graphe(g)
    gr.charge_cache() # nœud_of_rue
    print("Chargement du graphe fini.\n")
    return gr



# Choix de la fonction à utiliser. (J'ai supprimé les autres de toute façon!)
charge_graphe = charge_graphe_bbox

g = charge_graphe(bavard=1)

# Pour télécharger une carte avec overpass : wget -O pau.osm "https://overpass.openstreetmap.ru/cgi/xapi_meta?*[bbox=-0.4285,43.2671,-0.2541,43.3403]"
#Agglo : wget -O pau.osm "https://overpass.openstreetmap.ru/cgi/xapi_meta?*[bbox=-0.48,43.26,-0.25,43.35]"




def élague_xml(chemin="données_inutiles/pau_agglo.osm"):
    """
    Entrée : chemin, chemin vers un fichier .osm
             chemin_sortie, autre chemin
    Effet : enregistre dans CHEMIN_XML (défini dans params.py) un .osm contenant uniquement les voies, leur id, et les ref des nœuds qui la composent du .osm initial.
    """

    print(f"Chargement du xml {chemin}")
    a = xml.parse(chemin).getroot()
    print("Création de l'arbre simplifié")
    res = xml.Element("osm")
    for c in a :
        if c.tag == "way":
            fils = xml.SubElement(res, "way")
            fils.attrib["id" ]= c.attrib["id"]
            for d in c:
                if d.tag=="nd":#Les nœuds osm sur le way c
                    petit_fils = xml.SubElement(fils, "nd")
                    petit_fils.attrib["ref"] = d.attrib["ref"]
    print("Enregistrement du xml simplifié")
    xml.ElementTree(res).write(CHEMIN_XML, encoding="utf-8")
    


#def init_tout():
    
