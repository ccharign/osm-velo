# -*- coding:utf-8 -*-


#################### Rajouter la ville aux données des nœuds ####################


#import overpy
#from récup_données import localisateur
from petites_fonctions import ajouteDico
import osmnx as ox
ox.config(use_cache=True, log_console=True)
from initialisation.params import CHEMIN_NŒUDS_VILLES, CHEMIN_JSON_NUM_COORDS


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
def nœuds_ville(ville):
    g = ox.graph_from_place({"city":ville, "country":"France"})
    return g.nodes


### Création du csv ###

def crée_csv():
    sortie = open(CHEMIN_NŒUDS_VILLES, "w")
    for ville in liste_villes():
        print("\n\n"+ville)
        sortie.write( ville + ";" + ",".join(map(str, nœuds_ville(ville))) + "\n")
    sortie.close()


def charge_csv():
    """ Renvoie le dico ville -> nœuds d’icelle"""
    res={}
    with open(CHEMIN_NŒUDS_VILLES) as entrée:
        for ligne in entrée:

            ville, suite = ligne.strip().split(";")
            nœuds = tuple(map(int, suite.split(",")))
            res[ville] = nœuds
    return res


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
