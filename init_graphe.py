# -*- coding:utf-8 -*-


import networkx as nx
import osmnx as ox
ox.config(use_cache=True, log_console=True)
from module_graphe import graphe #ma classe de graphe


# Pour la simplification dans osmnx :
# https://github.com/gboeing/osmnx-examples/blob/master/notebooks/04-simplify-graph-consolidate-nodes.ipynb

# filtrage
# https://stackoverflow.com/questions/63466207/how-to-create-a-filtered-graph-from-an-osm-formatted-xml-file-using-osmnx


def charge_graphe(zone = "Pau, France", option={"network_type":"all"}, bavard=0):
    try:
        g= ox.io.load_graphml(f'données/{zone}.graphml')
        if bavard:print("Graphe en mémoire !")
    except FileNotFoundError:
        if bavard:print("Graphe pas en mémoire. Chargement depuis osm.")
        g=ox.graph_from_place(zone, **option)
        if bavard:print("Chargement fini. Je l'enregistre pour la prochaie fois.")
        ox.io.save_graphml(g, f"données/{zone}.graphml")
    
    gr = graphe(g)
    gr.charge_cache() # nœud_of_rue
    return gr



# Pour télécharger une carte avec overpass : wget -O pau.osm "https://overpass.openstreetmap.ru/cgi/xapi_meta?*[bbox=-0.4285,43.2671,-0.2541,43.3403]"
#Agglo : wget -O pau.osm "https://overpass.openstreetmap.ru/cgi/xapi_meta?*[bbox=-0.48,43.26,-0.25,43.35]"

import xml.etree.ElementTree as xml # Manipuler le xml local

from params import CHEMIN_XML # Chemin du xml élagué


def élague_xml(chemin="données_inutiles/pau_agglo.osm"):
    """
    Entrée : chemin, chemin vers un fichier .osm
             chemin_sortie, autre chemin
    Effet : enregistre dans chemin_sortie un .osm contenant uniquement les voies, leur id, et les ref des nœuds qui la composent du .osm initial.

    Ne devrait servir qu'une fois. À mettre dans un module init ?

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
    
