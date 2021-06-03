# -*- coding:utf-8 -*-

# Ce module regroupe les fonctions de recherche de données géographiques qui n'utilisent pas osmnx

import geopy
#, overpy
from params import VILLE_DÉFAUT, LOG_PB, CHEMIN_XML, CHEMIN_JSON_NUM_COORDS
import xml.etree.ElementTree as xml  # Manipuler le xml local
import time
import re


geopy.geocoders.options.default_user_agent = "pau à vélo"

localisateur = geopy.geocoders.Nominatim(user_agent="pau à vélo")

def recherche_inversée(coords):
    time.sleep(1)
    return(localisateur.reverse(coords))
    
#api = overpy.Overpass()


class LieuPasTrouvé(Exception):
    pass


# Pour contourner le pb des tronçons manquant dans Nominatim :
# 1) récupérer le nom osm de la rue
# 2) recherche dans le graphe


def cherche_lieu(nom_rue, ville=VILLE_DÉFAUT, pays="France", bavard=0):
    """ Renvoie la liste d'objets geopy enregistrées dans osm pour la rue dont le nom est passé en argument. On peut préciser un numéro dans nom_rue.
    """
    try:
        #  Essai 1 : recherche structurée. Ne marche que si l'objet à chercher est effectivement une rue
        if bavard > 1: print(f'Essai 1: "street":{nom_rue}, "city":{ville}, "country":{pays}')
        lieu = localisateur.geocode( {"street":nom_rue, "city":ville, "country":pays, "dedup":0}, exactly_one=False, limit=None  ) # Autoriser plusieurs résultats car souvent une rue est découpée en plusieurs tronçons
        if lieu is not None:
            return lieu
        else:
            # Essai 2: non structuré. Risque de tomber sur un résultat pas dans la bonne ville.
            LOG_PB(f"La recherche structurée a échouée pour {nom_rue, ville}.")
            print("Recherche Nominatim non structurée... Attention : résultat pas fiable.")
            print(f'Essai 2 : "{nom_rue}, {ville}, {pays}" ')
            lieu = localisateur.geocode(f"{nom_rue}, {ville}, {pays}", exactly_one=False)
            if lieu is not None:
                return lieu
            else:
                raise LieuPasTrouvé
    except Exception as e:
        print(e)
        LOG_PB(f"{e}\n Lieu non trouvé : {nom_rue} ({ville})")






def infos_nœud(id_nœud):
    r = api.query(f"""
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


print(f"Chargement du xml {CHEMIN_XML}")
root = xml.parse(CHEMIN_XML).getroot()
print("fini\n")


def nœuds_sur_tronçon_local(id_rue):
    """ Cherche les nœuds d'une rue dans le fichier local. Renvoie la liste des nœuds trouvés (int list).
    """

    for c in root:
        if c.tag == "way" and c.attrib["id"] == str(id_rue):
            return [int(truc.attrib["ref"]) for truc in c if truc.tag == "nd"]
    return []  #  Si rien de trouvé


def nœuds_sur_rue_local(nom_rue, ville=VILLE_DÉFAUT, pays="France", bavard=0):
    rue = cherche_lieu(nom_rue, ville=ville, pays=pays, bavard=bavard)
    if bavard: print(rue)
    res = []
    for tronçon in rue:  #  A priori, cherche_lieu renvoie une liste
        if tronçon.raw["osm_type"] == "node":
            if bavard: print(f"Récupéré directement un nœud osm ({tronçon.raw['osm_id']}) pour {nom_rue} ({ville}). Je renvoie le premier de la liste.")
            return [tronçon.raw["osm_id"]]
        elif tronçon.raw["osm_type"] == "way":
            id_rue = tronçon.raw["osm_id"]
            if bavard: print(f"Je cherche les nœuds de {nom_rue} dans le tronçon {id_rue}.")
            res.append(nœuds_sur_tronçon_local(id_rue))
    nœuds_sur_tronçons = tronçons_rassemblés(res)

    if len(nœuds_sur_tronçons) > 1:
        print(f"  -- Je n’ai pas pu rassembler les tronçons pour {nom_rue}. --")
        res = []
        for t in nœuds_sur_tronçons:
            res.extend(t)
            return res
    else:
        return nœuds_sur_tronçons[0]


def nœuds_of_adresse(adresse, ville=VILLE_DÉFAUT, pays="France", bavard=0):
    """ Entrée : une adresse, càd au minimum un numéro et un nom de rue.
        Sortie : liste des nœuds osm récupérés via Nominatim.
    """
    pass




########## Interpolation des adresses ##########

def charge_rue_num_coords():
    """ Renvoie le dictionnaire ville -> rue -> parité -> liste des (numéros, coords)"""
    entrée = open(CHEMIN_JSON_NUM_COORDS)
    res = {}
    for ligne in entrée:
        villerue, tmp = ligne.strip().split(":")
        ville, rue = villerue.split(";")
        données = tmp.split(";")
        if ville not in res: res[ville] = {}
        res[ville][rue] = ([], [])  # numéros pairs, numéros impairs

        for k in range(2):
            if données[k] != "":
                for x in données[k].split("|"):
                    num, lat, lon = x.split(",")
                    res[ville][rue][k].append((int(num), (float(lat), float(lon))))
    return res

D_RUE_NUM_COORDS = charge_rue_num_coords()

def sauv_rue_nom_coords(d=D_RUE_NUM_COORDS):
    """ Sauvegarde le dico ville -> rue -> parité -> liste des (numéros, coords) dans le fichier CHEMIN_JSON_NUM_COORDS.
    Format :
    Une ligne pour chaque couple (ville,rue).
    ville; rue : liste_pairs;liste_impairs
    Où liste_pairs et liste_impairs sont des (num, lat, lon) séparés par des |
    """
    sortie = open(CHEMIN_JSON_NUM_COORDS,"w")
    for rue in d.keys():
        for ville in d[rue].keys():
            pairs   = [ str((num,lat,lon))[1:-1] for (num,(lat,lon)) in d[rue][ville][0]]
            impairs = [ str((num,lat,lon))[1:-1] for (num,(lat,lon)) in d[rue][ville][1]]
            à_écrire = "|".join(pairs)+";"+"|".join(inpairs)
            sortie.write(à_écrire+"\n")
    

def barycentre(c1, c2, λ):
    """ Entrée : c1,  c2 des coords
                 λ ∈ [0,1]
        Sortie : λc1 + (1-λ)c2"""
    return (λ*c1[0]+(1-λ)*c2[0], λ*c1[1]+(1-λ)*c2[1])


def coords_of_adresse(num, rue, ville=VILLE_DÉFAUT, pays="France"):
    """ Cherche les coordonnées de l’adresse fournie en interpolant parmi les adresses connues."""
    
    nom_ville = re.findall("[0-9]*\ ?([^0-9]*)", ville)[0]
    try:
        k = num % 2  # parité du numéro
        l = D_RUE_NUM_COORDS[nom_ville][rue][k]
        if len(l) < 2:
            return None
        else:
            deb, c1 = -1, (-1, -1)
            fin, c2 = -1, (-1, -1)
            for (n, c) in l:
                if n <= num:
                    deb, c1 = n, c
                if n >= num:
                    fin, c2 = n, c
                    break
            if (deb, c1) == (-1, (-1, -1)):  # num est plus petit que tous les éléments de l
                ((deb, c1), (fin, c2)) = l[:2]
            elif (fin, c2) == (-1, (-1, -1)):  # num est plus grand que tous les éléments de l
                ((deb, c1), (fin, c2)) = l[-2:]
            λ  = (num-fin)/(deb-fin)
            return barycentre(c1, c2, λ)
    
    except KeyError as e:
        print(f"Pas de données pour {e}")
        return None



def kilométrage_piéton():
    """ Rien à voir : calcul du kilométrage de voies marquées « pedestrian » ou « footway »."""
    res = []
    for c in root:
        if c.tag == "way":
            for truc in c:
                if truc.tag == "tag" and truc.attrib["k"] == "highway" and truc.attrib["v"] in ["pedestrian", "footway"] :
                    res.append(c)
    for c in res:
        for truc in c:
            if truc.tag == "tag" and truc.attrib["k"] == "name": print(truc.attrib["v"])
# #Faire une classe Nœud_OSM pour extraire les tags, les nœuds d'une voie etc
