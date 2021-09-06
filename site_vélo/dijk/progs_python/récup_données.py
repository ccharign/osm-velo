# -*- coding:utf-8 -*-

# Ce module regroupe les fonctions de recherche de données géographiques qui n'utilisent pas osmnx, pour utilisation à chaque utilisation.
# Les fonctions d’analyse de données plus lentes depuis le .osm qui ont vocation à n’être utilisées qu’une fois (ou lors des mise à jour des données osm) sont dans le dossier initialisation.

import geopy
#, overpy
from params import LOG_PB, CHEMIN_XML, CHEMIN_JSON_NUM_COORDS
from lecture_adresse.normalisation import normalise_rue, normalise_ville, VILLE_DÉFAUT
import xml.etree.ElementTree as xml  # Manipuler le xml local
import time
import re
from lecture_adresse.normalisation import normalise_rue, normalise_ville


geopy.geocoders.options.default_user_agent = "pau à vélo"
localisateur = geopy.geocoders.Nominatim(user_agent="pau à vélo")


def recherche_inversée(coords, bavard=0):
    if bavard>0:print("Pause de 1s avant la recherche inversée")
    time.sleep(1)
    return(localisateur.reverse(coords))
    
#api = overpy.Overpass()


class LieuPasTrouvé(Exception):
    pass


# Pour contourner le pb des tronçons manquant dans Nominatim :
# 1) récupérer le nom osm de la rue
# 2) recherche dans le graphe


def cherche_lieu(adresse, bavard=0):
    """
    adresse (instance de Adresse)

    Renvoie la liste d'objets geopy enregistrées dans osm pour la rue dont le nom est passé en argument. On peut préciser un numéro dans nom_rue.
    """
    nom_rue = adresse.rue
    ville=adresse.ville
    pays=adresse.pays
    #  Essai 1 : recherche structurée. Ne marche que si l'objet à chercher est effectivement une rue
    if bavard > 1: print(f'Essai 1: "street":{nom_rue}, "city":{ville.avec_code()}, "country":{pays}')
    lieu = localisateur.geocode( {"street":nom_rue, "city":ville.avec_code(), "country":pays, "dedup":0}, exactly_one=False, limit=None  ) # Autoriser plusieurs résultats car souvent une rue est découpée en plusieurs tronçons
    if lieu is not None:
        return lieu

    else:
        # Essai 2: non structuré. Risque de tomber sur un résultat pas dans la bonne ville.
        LOG_PB(f"La recherche structurée a échouée pour {adresse}.")
        print("Recherche Nominatim non structurée... Attention : résultat pas fiable.")
        print(f'Essai 2 : "{adresse.pour_nominatim()}" ')
        lieu = localisateur.geocode(f"{adresse.pour_nominatim()}", exactly_one=False)
        if lieu is not None:
            return lieu
        else:
            raise LieuPasTrouvé(f"{adresse}")







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


def coords_lieu(nom_rue, ville= VILLE_DÉFAUT, pays="France", bavard=0):
    """ Renvoie les coordonnées du lieu obtenues par une recherche Nominatim"""
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
        ville = normalise_ville(ville)
        rue = normalise_rue(rue, ville)
        données = tmp.split(";")
        ville_n=ville.nom
        if ville_n not in res: res[ville_n] = {}
        res[ville_n][rue] = ([], [])  # numéros pairs, numéros impairs

        for k in range(2):
            if données[k] != "":
                for x in données[k].split("|"):
                    num, lat, lon = x.split(",")
                    res[ville_n][rue][k].append((int(num), (float(lat), float(lon))))
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
    for ville in d.keys():
        villen = normalise_ville(ville)
        for rue in d[ville].keys():
            ruen = normalise_rue(rue)
            pairs   = [ str((num,lat,lon))[1:-1] for (num,(lat,lon)) in d[ville][rue][0] ]
            impairs = [ str((num,lat,lon))[1:-1] for (num,(lat,lon)) in d[ville][rue][1] ]
            à_écrire = f"{villen};{ruen}:" + "|".join(pairs) + ";" + "|".join(impairs)
            sortie.write(à_écrire+"\n")
    

def barycentre(c1, c2, λ):
    """ Entrée : c1,  c2 des coords
                 λ ∈ [0,1]
        Sortie : λc1 + (1-λ)c2"""
    return (λ*c1[0]+(1-λ)*c2[0], λ*c1[1]+(1-λ)*c2[1])


class CoordsPasTrouvées(Exception):
    pass


def coords_of_adresse(adresse, bavard=0):
    """ Cherche les coordonnées de l’adresse fournie en interpolant parmi les adresses connues."""

    num=adresse.num
    ville=adresse.ville
    rue=adresse.rue_norm
    
    k = num % 2  # parité du numéro
    if rue not in D_RUE_NUM_COORDS[str(ville)]:
        raise CoordsPasTrouvées(f"Rue inconnue : {adresse.rue} (normalisé en {rue}).")
    l = D_RUE_NUM_COORDS[str(ville)][rue][k]
    if len(l) < 2:
        raise CoordsPasTrouvées(f"J’ai {len(l)} numéro en mémoire pour {rue} ({ville}) du côté de parité {k}. Je ne peux pas interpoler.")

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
        if bavard>0: print(f"Je connais les coords des numéros {deb} et {fin} de la rue {rue}")
        if deb==fin:
            return c1
        else:
            λ  = (num-fin)/(deb-fin)
            return barycentre(c1, c2, λ)





    
### Rien à voir ### 


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
