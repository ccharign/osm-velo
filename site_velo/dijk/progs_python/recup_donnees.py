# -*- coding:utf-8 -*-

# Ce module regroupe les petiter fonctions de recherche de données géographiques qui utilisent Nominatim, overpass, ou data.gouv.

import geopy
import overpy
from params import LOG_PB, CHEMIN_XML, CHEMIN_RUE_NUM_COORDS
#from lecture_adresse.normalisation import normalise_rue, normalise_ville, Adresse
from petites_fonctions import LOG
import xml.etree.ElementTree as xml  # Manipuler le xml local
import time
import re
#from lecture_adresse.normalisation import normalise_rue, normalise_ville
import requests
import json
import urllib.parse

geopy.geocoders.options.default_user_agent = "pau à vélo"
localisateur = geopy.geocoders.Nominatim(user_agent="pau à vélo")



    



class LieuPasTrouvé(Exception):
    pass


### Avec data.gouv ###

def cherche_adresse_complète(adresse, bavard=0):
    """
    Entrée : une adresse avec numéro de rue.
    Sortie : coordonnées (lon, lat) gps de cette adresse obtenue avec api-adresse.data.gouv.fr
    """
    # https://perso.esiee.fr/~courivad/python_bases/15-geo.html
    api_url = "https://api-adresse.data.gouv.fr/search/?q="
    r = requests.get(api_url + urllib.parse.quote(str(adresse)))
    r = r.content.decode('unicode_escape')
    return json.loads(r)["features"][0]["geometry"]["coordinates"]


#https://adresse.data.gouv.fr/api-doc/adresse
def rue_of_coords(c, bavard=0):
    """
    Entrée : (lon, lat)
    Sortie : (nom, ville, code de postal) de la rue renvoyé par adresse.data.gouv
    """
    lon, lat = c
    api_url = f"https://api-adresse.data.gouv.fr/reverse/?lon={lon}&lat={lat}&type=street"
    r = requests.get(api_url).content.decode('unicode_escape')
    d = json.loads(r)["features"][0]["properties"]
    res = d["name"], d["city"], int(d["postcode"])
    LOG(f"(rue_of_coords) Pour les coordonnées {c} j'ai obtenu {res}.", bavard=bavard)
    return res



### Avec Nominatim ###

def cherche_lieu(adresse, seulement_structurée=False, seulement_non_structurée=False, bavard=0):
    """
    Entrée : adresse (instance de Adresse)

    Sortie : liste d'objets geopy enregistrées dans osm pour la rue dont le nom est passé en argument. On peut préciser un numéro dans nom_rue.

    Premier essai : recherche structurée avec adresse.nom_rue et adresse.ville.avec_code
    Deuxième essai, seulement si seulement_structurée==False : non structurée avec essai adresse.pour_nominatim().
    """
    nom_rue = adresse.rue()
    ville = adresse.ville
    pays = adresse.pays
    
    if not seulement_non_structurée:
        #  Essai 1 : recherche structurée. Ne marche que si l'objet à chercher est effectivement une rue
        LOG(f'Essai 1: "street":{nom_rue}, "city":{ville.avec_code()}, "country":{pays}', bavard=bavard)
        lieu = localisateur.geocode( {"street":nom_rue, "city":ville.avec_code(), "country":pays, "dedup":0}, exactly_one=False, limit=None  ) # Autoriser plusieurs résultats car souvent une rue est découpée en plusieurs tronçons
        if lieu is not None:
            return lieu
        else:
            LOG_PB(f"La recherche structurée a échouée pour {adresse}.")

    if not seulement_structurée:
        # Essai 2: non structuré. Risque de tomber sur un résultat pas dans la bonne ville.
        LOG(f'Essai 2 : "{adresse.pour_nominatim()}" ', bavard=bavard)
        lieu = localisateur.geocode(f"{adresse.pour_nominatim()}", exactly_one=False)
        if lieu is not None:
            return lieu
        else:
            raise LieuPasTrouvé(f"{adresse}")


### Avec overpass ###

def nœuds_of_rue(adresse, bavard=0):
    """
    Sortie : liste des nœuds osm correspondant aux ways correspondant à l'adresse.
    """

    lieu = cherche_lieu(adresse, seulement_non_structurée=True , bavard=bavard)
    if bavard>0:print(f"rd.nœuds_of_rue : la recherche Nominatim pour {adresse} a donné {lieu}.")
    res = []

    ids_way = [truc.raw["osm_id"] for truc in lieu if truc.raw["osm_type"]=="way"]
    ids_node = [truc.raw["osm_id"] for truc in lieu if truc.raw["osm_type"]=="node"]
    if bavard>0:print(f"Voici les ids_way trouvés : {ids_way}")
    if len(ids_way)>0:
        return nœuds_of_idsrue(ids_way, bavard=bavard-1)
    elif len(ids_node)>0:
        return ids_node
    else:
        return []
    # for truc in lieu:
    #     if truc.raw["osm_type"]=="way":
    #         id_way = truc.raw["osm_id"]
    #         res.extend(nœuds_of_idrue(id_way))
    # return res

    
def bb_enveloppante(nœuds, bavard=0):
    """
    Entrée : nœuds (int iterable), liste d’id_osm de nœuds
    Sortie : la plus petite bounding box contenant ces nœuds.
    """
    api = overpy.Overpass()
    req = f"""
    node(id:{",".join(map( str, nœuds))});
    out;
    """
    if bavard>0: print(req)
    rés = api.query(req).nodes
    lons = [n.lon for n in rés]
    lats = [n.lat for n in rés]
    # bb :sone
    return float(min(lats)), float(min(lons)), float(max(lats)), float(max(lons))


def nœuds_dans_bb(bb, tol=0):
    """
    Entrée : bb, bounding box (s,o,n,e)
             tol (float>=0)
             dtol (float >0)
    Sortie : liste des nœuds osm trouvés dans la bb.
    """
    print("J’attends 5s pour overpass.")
    time.sleep(5)
    api=overpy.Overpass()
    s,o,n,e = bb
    req = f"node({s-tol}, {o-tol}, {n+tol}, {e+tol});out;"
    return [n.id for n in api.query(req).nodes]
    
    

def ways_contenant_nodes(nœuds):
    """
    Entrée : nœuds (int itérable), id_osm de nœuds
    Sortie : liste des ways avec tag highwaycontenant au moins un élément de nœuds.
    """
    api = overpy.Overpass()
    requête=f"""
    node(id:{",".join(map( str, nœuds))});
    way[highway](bn);
    out;
    """
    return api.query(requête).ways


def nœuds_reliés(nœuds):
    """
    Entrée : itérable de nœuds osm
    Sortie : liste des nœuds sur un way contenant un des nœuds de nœuds.
    """
    ways = ways_contenant_nodes(nœuds)
    res=[]
    for w in ways:
        res.extend(w._node_ids)
    return res

# nœuds de place saint louis de gonzague = [782224313, 782408135, 8428498156, 782155281, 343660472, 782224313]

def nœuds_of_idsrue(ids_rue, bavard=0):
    """
    Entrée : ids_rue (int itérable), ids osm de ways.
    Sortie : liste des nœuds de celles-ci.
    """
    assert len(list(ids_rue))>0, f"(rd.nœuds_of_idsrue) J’ai reçu ids_rue={list(ids_rue)}"
    api = overpy.Overpass()
    requête=f"""
            way(id:{",".join(map(str, ids_rue))});
            out;"""
    if bavard>0:print(requête)
    print("J’attends 5s pour overpass.")
    time.sleep(5)
    res_req = api.query(requête)
    res=[]
    for w in res_req.ways:
        res.extend(w._node_ids)
    return res


def villes_of_bbox(bbox):
    requête="""[out:json][timeout:25];
// gather results
(
  node["place"~"city|town|village|hamlet"]({{bbox}});
  way["place"="village"]({{bbox}});
  relation["place"="village"]({{bbox}});
);
// print results
out body;
>;
out skel qt;"""


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


# def coords_lieu(adresse, bavard=0):
#     """ Renvoie les coordonnées du lieu obtenues par une recherche Nominatim"""
    
#     lieu = cherche_lieu(adresse, bavard=bavard)[0]
#     return lieu.latitude, lieu.longitude







###################################################
#####          Recherche en local             #####
###################################################

# Plus utilisé car lent...


def nœuds_sur_tronçon_local(id_rue):
    """ Cherche les nœuds d'une rue dans le fichier local. Renvoie la liste des nœuds trouvés (int list).
    """
    try:
        print(f"Chargement du xml {CHEMIN_XML}")
        root = xml.parse(CHEMIN_XML).getroot()
        print("fini\n")
    except Exception as e:
        print(f"Le chargement du fichier osm élagué a échoué, {e}.")

    for c in root:
        if c.tag == "way" and c.attrib["id"] == str(id_rue):
            return [int(truc.attrib["ref"]) for truc in c if truc.tag == "nd"]
    return []  #  Si rien de trouvé


def nœuds_sur_rue_local(adresse, bavard=0):
    LOG_PB(f"J’ai eu besoin de recup_donnees.nœuds_sur_rue_local pour {adresse}.")
    rue = cherche_lieu(adresse, bavard=bavard)
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




########## Interpolation des adresses ##########
## Plus utilisé maintenant pour la France puisqu'il y a data.gouv

def charge_rue_num_coords():
    """ Renvoie le dictionnaire ville -> rue -> parité -> liste des (numéros, coords)"""
    entrée = open(CHEMIN_RUE_NUM_COORDS, encoding="utf-8")
    res = {}
    for ligne in entrée:
        villerue, tmp = ligne.strip().split(":")
        ville, rue = villerue.split(";")
        ville = normalise_ville(ville)
        rue = normalise_rue(rue, ville)
        données = tmp.split(";")
        ville_n=ville.nom_norm
        if ville_n not in res: res[ville_n] = {}
        res[ville_n][rue] = ([], [])  # numéros pairs, numéros impairs

        for k in range(2):
            if données[k] != "":
                for x in données[k].split("|"):
                    num, lat, lon = x.split(",")
                    res[ville_n][rue][k].append((int(num), (float(lat), float(lon))))
    return res

#print("Chargement du dictionnaire ville -> rue -> parité -> liste des (numéros, coords).")
#D_RUE_NUM_COORDS = charge_rue_num_coords()


def sauv_rue_nom_coords(d=None):
    """ Sauvegarde le dico ville -> rue -> parité -> liste des (numéros, coords) dans le fichier CHEMIN_JSON_NUM_COORDS.
    Format :
    Une ligne pour chaque couple (ville,rue).
    ville; rue : liste_pairs;liste_impairs
    Où liste_pairs et liste_impairs sont des (num, lat, lon) séparés par des |
    """
    if d is None:
        d=charge_rue_num_coords()
    sortie = open(CHEMIN_JSON_NUM_COORDS,"w", encoding="utf-8")
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

    LOG_PB(f"J’ai eu besoin de recup_donnees.coords_of_adresse")
    D_RUE_NUM_COORDS = charge_rue_num_coords()
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
