# -*- coding:utf-8 -*-

# Ce module regroupe les fonctions de recherche de données géographiques qui n'utilisent pas osmnx

import geopy, overpy
#import functools


# Pour télécharger une carte avec overpass : wget -O pau.osm "https://overpass.openstreetmap.ru/cgi/xapi_meta?*[bbox=-0.4285,43.2671,-0.2541,43.3403]"
import xml.etree.ElementTree as xml # Manipuler le xml local

CHEMIN_XML = "données/voies_et_nœuds.osm" #Adresse du fichier .osm utilisé pour chercher les nœuds d'une rue.


geopy.geocoders.options.default_user_agent = "pau à vélo"

localisateur = geopy.geocoders.osm.Nominatim(user_agent="pau à vélo")
#geocode = functools.lru_cache(maxsize=128)(functools.partial(localisateur.geocode, timeout=5)) #mémoïzation
api = overpy.Overpass()

def cherche_lieu(nom_rue, ville=64000, pays="France", bavard=0):
    """ Renvoie la liste d'objets geopy enregistrées dans osm pour la rue dont le nom est passé en argument. On peut préciser un numéro dans nom_rue.
    """
    try:
        #Essai 1 : recherche structurée. Ne marche que si l'objet à chercher est effectivement une rue
        if bavard>1:print(f'Essai 1: "street":{nom_rue}, "city":{ville}, "country":{pays}')
        lieu = localisateur.geocode( {"street":nom_rue, "city":ville, "country":pays, "dedup":0}, exactly_one=False  ) # Autoriser plusieurs résultats car souvent une rue est découpée en plusieurs tronçons
        if lieu != None:
            return lieu
        else:
            # Essai 2: non structuré. Risque de tomber sur un résultat pas dans la bonne ville.
            print("Recherche Nominatim non structurée... Attention : résultat pas fiable")
            print(f'Essai 2 : "{nom_rue}, {ville}, {pays}" ')
            lieu = localisateur.geocode( f"{nom_rue}, {ville}, {pays}", exactly_one=False  )
            if lieu != None:
                return lieu
            else:
                raise NotFound
    except:
        print(f"lieu non trouvé : {nom_rue} ({ville})")


def nœuds_sur_rue(nom_rue, ville="Pau", pays="France", bavard=1):

    res=[]
    
    # Partie 1 avec Nominatim je récupère l'id de la rue
    rue = cherche_lieu(nom_rue, ville=ville, pays=pays, bavard=bavard)
    
    for tronçon in rue : #A priori, cherche_lieu renvoie une liste
        id_rue = tronçon.raw["osm_id"]
        if bavard:print(f"id de {nom_rue} : {id_rue}")
    
        # Partie 2 avec Overpass je récupère les nœuds de cette rue
        
        r = api.query(f"way({id_rue});out;")
        rue = r.ways[0]
        nœuds = rue.get_nodes(resolve_missing=True)
        res.extend([n.id for n in nœuds])
    return res





def infos_nœud(id_nœud):
    r=api.query(f"""
    node({id_nœud});out;
    """)
    return r

def coord_nœud(id_nœud):
    n = api.query(f"""
    node({id_nœud});out;
    """).nodes[0]
    print(n)
    return float(n.lat), float(n.lon)
    

def coords_lieu(nom_rue, ville=64000, pays="France", bavard=0):
    lieu = cherche_lieu(nom_rue, ville=ville, pays=pays, bavard=bavard)[0]
    return lieu.latitude, lieu.longitude

#id_hédas="30845632"
#id_hédas2="37770876"



###################################################
#####          Recherche en local             #####
###################################################




def élague_xml(chemin="données_inutiles/pau.osm"):
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
    



root = xml.parse(CHEMIN_XML).getroot()

def nœuds_sur_tronçon_local(id_rue):
    """ Cherche les nœuds d'une rue dans le fichier local. Renvoie la liste des nœuds trouvés (int list).
    """

    for c in root:
        if c.tag == "way" and c.attrib["id"] == str(id_rue) :
            return [int(truc.attrib["ref"]) for truc in c if truc.tag=="nd"]
        

def nœuds_sur_rue_local(nom_rue,ville="64000", pays="France",bavard=0):
    rue = cherche_lieu(nom_rue, ville=ville, pays=pays, bavard=bavard)
    if bavard:print(rue)
    res=[]
    for tronçon in rue : #A priori, cherche_lieu renvoie une liste
        id_rue = tronçon.raw["osm_id"]
        if bavard:print(f"Je cherche les nœuds de {nom_rue} dans le tronçon {id_rue}.")
        res.extend(nœuds_sur_tronçon_local(id_rue))
    return res


def kilométrage_piéton():
    "Rien à voir : calcul du kilométrage de voies marquées «pedestrian» ou «footway»."""
    res=[]
    for c in root:
        if c.tag=="way":
            for truc in c:
                if truc.tag == "tag" and truc.attrib["k"]=="highway" and truc.attrib["v"] in ["pedestrian", "footway"] :
                    res.append(c)
    for c in res:
        for truc in c:
            if truc.tag == "tag" and truc.attrib["k"]=="name":print(truc.attrib["v"])
#Faire une classe Nœud_OSM pour extraire les tags, les nœuds d'une voie etc
