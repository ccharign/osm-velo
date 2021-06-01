# -*- coding:utf-8 -*-

#import networkx as nx

from module_graphe import graphe  # ma classe de graphe
import xml.etree.ElementTree as xml  # Manipuler le xml local
from params import CHEMIN_XML, CHEMIN_XML_COMPLET, CHEMIN_JSON_NUM_COORDS  # Chemin du xml élagué
import re
import time
import osmnx.io
from récup_données import recherche_inversée, commune_of_adresse
import subprocess
#ox.config(use_cache=True, log_console=True)

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
        subprocess.call(["crée_graphe.py", nom_fichier])
        g = ox.io.load_graphml(nom_fichier)

    gr = graphe(g)
    gr.charge_cache()  # nœud_of_rue
    print("Chargement de la cyclabilité")
    gr.charge_cycla()
    print("Chargement du graphe fini.\n")
    return gr






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


def normalise_ville(ville):
    """En minuscule avec capitale majuscule."""
    return ville.title()


def commune_of_adresse(adr):
    """ Entrée : adresse renvoyée par Nominatim.reveres.
        Sortie : la commune (on espère)"""
    à_essayer = ["city", "village", "town"]
    for clef in à_essayer:
        try:
            return adr[clef]
        except KeyError :
            pass



def extrait_rue_num_coords(chemin="données_inutiles/pau.osm", bavard=0):
    """ Entrée : fichier xml d’openstreetmap
        Effet : crée un fichier texte associant à chaque rue la list des (numéro connu, coords correspondantes)"""
    

    print("Chargement du xml")
    a = xml.parse("données_inutiles/pau.osm").getroot()
    
    print("Extraction des adresses connues")
    
    def ajoute_dans_res(villerue, val):
        if villerue not in res:
            res[villerue] = []
        res[villerue].append(val)
        
    res = {}
    nums_seuls = []
    for c in a:
        if c.tag == "node":  # Sinon on n’a pas les coords.
            # Voyons si nous disposons d’une adresse pour ce nœud.
            num, rue, ville = None, None, None
            for d in c:
                if d.tag == "tag" and d.attrib["k"] == "addr:housenumber":
                    num = d.attrib["v"]
                if d.tag == "tag" and d.attrib["k"] == "addr:street":
                    rue = d.attrib["v"]
                if d.tag == "tag" and d.attrib["k"] == "addr:city":
                    ville = normalise_ville(d.attrib["v"])
            if num is not None:
                try:
                    num = int_of_num(num)
                    if rue is not None and num is not None and ville is not None:
                        ajoute_dans_res(ville+";"+rue, (num, float(c.attrib["lat"]), float(c.attrib["lon"])))
                    else:
                        # juste un numéro
                        nums_seuls.append( (c.attrib["id"], num, float(c.attrib["lat"]), float(c.attrib["lon"])) )
                except Exception as e:  # pb dans le xml
                    print(f"Pb à  la lecture du nœud {num, rue, ville}  : {e}.\n Nœud abandonné.")
            


    print("Recherche des rues des numéros orphelins")
    print("Recherche inversée Nominatim limitée à une recherche par seconde...")
    nb=0
    for id_node, num, lat, lon in nums_seuls:
        try:
            adresse = recherche_inversée((lat, lon)).raw["address"]
            if bavard>0: print(adresse)
            villerue = commune_of_adresse(adresse) + ";"+adresse["road"]
            ajoute_dans_res(villerue, (num, lat, lon))
            nb+=1
        except Exception as e:
            print(f"Erreur pour {id_node, num, lat, lon} : {e}")
    print(f"{nb} adresses collectées")
        
    print("Écriture du fichier")
    sortie = open(CHEMIN_JSON_NUM_COORDS, "w")
    for villerue, l in res.items():
        if len(l) > 1:  # Une seule adresse dans la rue ça ne permet pas d’interpoler.
            l_pair = [x for x in l if x[0]%2 == 0]
            l_impair = [x for x in l if x[0]%2 != 0]
            
            def à_écrire(ll):
                ll.sort()
                ll = [ x for i,x in enumerate(ll) if i==0 or x[0]!=ll[i-1][0] ]  # dédoublonnage des numéros
                if bavard: print(à_écrire)
                return "|".join([str(c)[1:-1] for c in ll])
                
            sortie.write(f"{villerue}:{';'.join([à_écrire(l_pair), à_écrire(l_impair)])}\n")
    sortie.close()
    #return nums_seuls
