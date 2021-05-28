# -*- coding:utf-8 -*-

import networkx as nx
import osmnx as ox
from module_graphe import graphe  # ma classe de graphe
import xml.etree.ElementTree as xml  # Manipuler le xml local
from params import CHEMIN_XML, CHEMIN_XML_COMPLET, CHEMIN_JSON_NUM_COORDS  # Chemin du xml élagué
import re
ox.config(use_cache=True, log_console=True)

# Pour la simplification dans osmnx :
# https://github.com/gboeing/osmnx-examples/blob/master/notebooks/04-simplify-graph-consolidate-nodes.ipynb

# filtrage
# https://stackoverflow.com/questions/63466207/how-to-create-a-filtered-graph-from-an-osm-formatted-xml-file-using-osmnx




def charge_graphe_bbox(ouest=-0.4285, sud=43.2671, est=-0.2541, nord=43.3403, option={"network_type":"all"}, bavard=1):
    nom_fichier = f'données/{ouest}{sud}{est}{nord}.graphml'
    try:
        g = ox.io.load_graphml(nom_fichier)
        if bavard: print("Graphe en mémoire !")
    except FileNotFoundError:
        if bavard: print(f"Graphe pas en mémoire à {nom_fichier}. Chargement depuis osm.")
        g = ox.graph_from_bbox(nord, sud, est, ouest, **option)
        print("conversion en graphe non orienté")
        g = ox.get_undirected(g)
        if bavard: print("Chargement fini. Je l'enregistre pour la prochaine fois.")
        ox.io.save_graphml(g, nom_fichier)

    gr = graphe(g)
    gr.charge_cache()  # nœud_of_rue
    print("Chargement de la cyclabilité")
    gr.charge_cycla()
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
    Effet : enregistre dans CHEMIN_XML (défini dans params.py) un .osm contenant uniquement les voies, leur id, leur nom et les ref des nœuds qui la composent du .osm initial.
    """

    print(f"Chargement du xml {chemin}")
    a = xml.parse(chemin).getroot()
    print("Création de l'arbre simplifié")
    res = xml.Element("osm")
    for c in a:
        if c.tag == "way":
            fils = xml.SubElement(res, "way")
            fils.attrib["id"] = c.attrib["id"]
            
            for d in c:
                if d.tag == "nd":  # Les nœuds osm sur le way c
                    petit_fils = xml.SubElement(fils, "nd")
                    petit_fils.attrib["ref"] = d.attrib["ref"]
                elif d.tag == "tag" and d.attrib["k"] == "name":  # le nom de c
                    petit_fils = xml.SubElement(fils, "tag")
                    petit_fils.attrib["k"] = "name"
                    petit_fils.attrib["v"] = d.attrib["v"]
    print("Enregistrement du xml simplifié")
    xml.ElementTree(res).write(CHEMIN_XML, encoding="utf-8")


def coords_of_nœud_xml(c):
    return float(c.attrib["lat"]), float(c.attrib["lon"])


def int_of_num(n, bavard=0):
    """ Entrée : une chaîne représentant un numéro de rue.
        Sortie : ce numéro sous forme d’entier. Un éventuel "bis" ou "ter" sera supprimé."""
    e = re.compile("\ *([0-9]*)[^0-9]*$")
    if bavard : print(n, re.findall(e, n))
    num = re.findall(e, n)[0]
    return int(num)


def extrait_rue_num_coords(chemin="données_inutiles/pau.osm", bavard=0):
    """ Entrée : fichier xml d’openstreetmap
        Effet : crée un json associant à chaque rue la list des (numéro connu, coords correspondantes)"""

    print("Chargement du xml")
    a = xml.parse(chemin).getroot()

    print("Extraction des adresses connues")
    res = {}
    for c in a:
        if c.tag == "node":
            # Voyons si nous disposons d’une adresse pour ce nœud.
            num, rue = None, None
            for d in c:
                if d.tag == "tag" and d.attrib["k"] == "addr:housenumber":
                    num = d.attrib["v"]
                if d.tag == "tag" and d.attrib["k"] == "addr:street":
                    rue = d.attrib["v"]
            if rue is not None and num is not None:
                try:
                    num = int_of_num(num)
                    if rue in res:
                        res[rue].append((num, float(c.attrib["lat"]), float(c.attrib["lon"])))
                    else:
                        res[rue] = [(num, float(c.attrib["lat"]), float(c.attrib["lon"]))]
                except:  # pb dans le xml
                    pass

    sortie = open(CHEMIN_JSON_NUM_COORDS, "w")
    print("Écriture du fichier")
    for rue, l in res.items():
        if len(l)>1:  # Une seule adresse dans la rue ça ne permet pas d’interpoler.
            l.sort()
            à_écrire = "|".join([str(c) for c in l])
            if bavard: print(à_écrire)
            sortie.write(f"{rue}:{à_écrire}\n")
    sortie.close()
