# -*- coding:utf-8 -*-


#################### Rajouter la ville aux données des nœuds ####################


import overpy
#from récup_données import localisateur
from params import CHEMIN_NŒUDS_VILLES, CHEMIN_JSON_NUM_COORDS
from petites_fonctions import ajouteDico
#from dijk.models import Ville, Sommet
from lecture_adresse.normalisation import normalise_ville
import osmnx as ox
ox.config(use_cache=True, log_console=True)



def liste_villes():
    """ Liste des villes apparaissant dans CHEMIN_JSON_NUM_COORDS."""
    res = set([])
    with open(CHEMIN_JSON_NUM_COORDS) as f:
        for ligne in f:
            res.add(ligne.split(";")[0])
    return res




# pour test : id de Pau 162431

# # Trop lent... Récupérer direct le .osm de chaque ville ?
# def nœuds_ville(ville):
#     """ Renvoie la liste des nœeud de ville.
#     Utilise Nominatim pour trouver la relation qui décrit la ville puis overpass pour le résultat final.
#     Semble extrêmement lent !
#     """
#     r = localisateur.geocode({"city":ville, "country":"France"}).raw
#     assert r["osm_type"] == "relation"
#     id_ville = r["osm_id"]
#     api = overpy.Overpass()
#     r = api.query(f"""
#     node(area:{3600000000+id_ville});
#     out ids;
#     """)
#     return r.node_ids


# Deuxième essai : avec osmnx
# Il manque certains nœuds !
# La simplification dans graph_from_place serait plus forte que celle lors de la création du graphe initial dans crée_graphe ?
def nœuds_ville(ville):
    g = ox.graph_from_place({"city":ville, "country":"France", "network_type":"all"})
    return g.nodes

## https://stackoverflow.com/questions/58844414/what-is-a-correct-overpass-turbo-query-for-getting-all-streets-in-a-city
#https://overpass-api.de/command_line.html
#wget "https://overpass-api.de/api/interpreter?data=node[name=\"Gielgen\"];out;"
def nœuds_ville2(ville, bavard=0):
    """ Ne fonctionne pas."""
    #requête = f"""area[name = "{ville}"]; (way(area)[highway]; ); (._;>;); out;"""
    requête = f"""area[name = "{ville}"][boundary=administrative]; way(area)[highway]; out;"""
    if bavard>0: print(requête)
    api=overpy.Overpass()
    res=set()
    res_ways = api.query(requête)
    for w in res_ways.ways:
        res.update(w._node_ids)
    return res

def test_overpass(id, bavard=0):
    #requête = f"""area[name = "{ville}"]; (way(area)[highway]; ); (._;>;); out;"""
    requête = f"""area[id = "{id}"]; way(area)[highway][name]; out;"""
    if bavard>0: print(requête)
    api=overpy.Overpass()
    return  api.query(requête)

### Création du csv ###

def crée_csv():
    sortie = open(CHEMIN_NŒUDS_VILLES, "w")
    for ville in liste_villes():
        print("\n\n"+ville)
        sortie.write( ville + ";" + ",".join(map(str, nœuds_ville(ville))) + "\n")
    sortie.close()


def charge_csv():
    """ Renvoie le dico ville -> nœuds d’icelle"""
    res = {}
    with open(CHEMIN_NŒUDS_VILLES) as entrée:
        for ligne in entrée:
            ville, suite = ligne.strip().split(";")
            nœuds = tuple(map(int, suite.split(",")))
            res[ville] = nœuds
    return res


def vérif_unicité_ville():
    """
    La réponse était False comme on pouvait s’en douter : certains nœuds sont dans plusieurs villes.
    """
    déjà_vus = set([])
    for ville, nœuds in charge_csv().items():
        for n in nœuds:
            if n in déjà_vus:
                return False
        déjà_vus.update(nœuds)
    return True





def ajoute_villes(g, bavard=0):
    """ Ajoute un champ "ville" à chaque arête de g qui contient une liste de villes.
    """
    compte=0
    with open(CHEMIN_NŒUDS_VILLES) as entrée:
        for ligne in entrée:

            ville, suite = ligne.strip().split(";")
            nœuds = set(map(int, suite.split(",")))
            for n in nœuds:
                if n in g.digraphe.nodes:
                    # Remplissage du graphe
                    for v in g.voisins_nus(n):
                        if v in nœuds:
                            ajouteDico( g.digraphe[n][v], "ville", ville )
                            ajouteDico( g.digraphe[v][n], "ville", ville )
                            compte+=1
    if bavard>0:
        print(f"{compte} noms de ville ajoutés")
