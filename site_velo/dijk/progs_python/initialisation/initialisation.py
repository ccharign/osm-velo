#!/usr/bin/python3
# -*- coding:utf-8 -*-

import os
import subprocess

if os.getcwd()=="/home/moi/git/osm vélo":
    os.chdir("site_velo/")
else :
    print(f"Dossier actuel: {os.getcwd()}")
    
import osmnx

from time import perf_counter
from dijk.progs_python.params import TMP, CHEMIN_RUE_NUM_COORDS, CHEMIN_NŒUDS_VILLES, CHEMIN_NŒUDS_RUES, DONNÉES, BBOX_DÉFAUT
from initialisation.crée_graphe import crée_graphe_bbox
#from initialisation.élaguage import élague_xml
from initialisation.numéros_rues import extrait_rue_num_coords
from initialisation.noeuds_des_rues import sortie_csv as csv_nœud_des_rues, extrait_nœuds_des_rues
from initialisation.ajoute_villes import crée_csv as csv_nœuds_des_villes, ajoute_villes, crée_csv_villes_of_nœuds
from lecture_adresse.normalisation import créationArbre, arbre_rue_dune_ville
from graphe_par_networkx import Graphe_nx
from petites_fonctions import sauv_fichier, chrono
#from networkx import read_graphml
from dijk.models import Ville, Zone
import initialisation.vers_django as vd


"""
Script pour réinitialiser ou ajouter une nouvelle zone.

Ce scrit ne réinitialise *pas* le cache ni la cyclabilité.
   -> À voir, peut être le cache ?
   -> Ou carrément recréer le cache...
   De toute façon le cache est assez peu utilisé me semble-t-il maintenant.
"""

def charge_multidigraph():
    """
    Renvoie le multidigraph de la zone défaut. Plutôt pour tests.
    """
    s,o,n,e = BBOX_DÉFAUT
    nom_fichier = f'{DONNÉES}/{s}{o}{n}{e}.graphml'
    g = osmnx.load_graphml(nom_fichier)
    return g



def charge_ville(nom, code, zone="Pau", ville_défaut=None, pays="France", bavard=2):

    ## Création de la ville dans Django et dans l'arbre lex
    ville_d = vd.nv_ville(nom, code)
    ## Création ou récupération de la zone
    if ville_défaut is not None:
        zone_d, _= Zone.objects.get_or_create(nom=zone, ville_défaut=Ville.objects.get(nom_complet=ville_défaut))
    else:
        zone_d = Zone.objects.get(nom=zone)

    ## Récup des graphe via osmnx
    print(f"Récupération du graphe pour « {code} {nom}, {pays} » avec une marge")
    gr_avec_marge = osmnx.graph_from_place(
        {"city":f"{nom}", "postcode":code, "country":pays},
        network_type="all", retain_all="True", buffer_dist=500
    )
    print("Récupération du graphe exact")
    gr_strict = osmnx.graph_from_place({"city":f"{nom}", "postcode":code, "country":pays}, network_type="all", retain_all="True")

    g = Graphe_nx(gr_avec_marge)
    
    ## Noms des villes
    print("Ajout du nom de ville.")
    for n in gr_strict.nodes:
        #if n not in g.villes_of_nœud: g.villes_of_nœud=[]
        g.villes_of_nœud[n] = [nom]

    ## nœuds des rues
    print("Calcul des nœuds de chaque rue")
    dico_rues = extrait_nœuds_des_rues(g, bavard=bavard-1) # dico ville -> rue -> liste nœuds # Seules les rues avec nom de ville, donc dans g_strict seront calculées.
    vd.charge_dico_rues_nœuds(ville_d, dico_rues[nom])
    print("Création de l'arbre lexicographique")
    arbre_rue_dune_ville(ville_d, dico_rues.keys())

    ## désorientation
    print("Désorientation du graphe")
    vd.désoriente(g, bavard=bavard-1)
    
    ## Transfert du graphe
    vd.transfert_graphe(g, zone_d, bavard=bavard-1, juste_arêtes=False)
    


def initialisation_sans_overpass(bbox=BBOX_DÉFAUT, aussi_nœuds_des_villes=False, force_téléchargement=False, bavard=1):
    """
    Entrée :
        bbox : (o, s, e, n) bounding box de la zone de laquelle récupérer les données.
        force_téléchargement : si True force la fonction à télécharger de nouveau le graphe depuis osm.
        aussi_nœuds_des_villes (bool) : pour recharger également les nœuds de chaque ville. Passe par un téléchargement du graphe de chaque ville via osmnx : un peu long.
    Effet :
       Initialise les données qui ne nécessitent pas un gros téléchargement depuis openstreetmap mais qui passent uniquement par osmnx.
       rema : Il faudrait voir comment s’y prend osmnx !

       Précisément, cette procédure crée :
             - le graphe au format graphml
             - nœuds_ville.csv (CHEMIN_NŒUDS_VILLES) qui donne les nœuds de chaque ville
             - nœuds_rues.csv (CHEMIN_NŒUDS_RUES) qui donne les nœuds de chaque rue
    """

    ## Création du graphe networkx
    s,o,n,e = bbox
    nom_fichier=f'{DONNÉES}/{s}{o}{n}{e}.graphml'
    if not force_téléchargement and os.path.exists(nom_fichier):
        #gr = read_graphml(nom_fichier, node_type=int)
        gr = osmnx.io.load_graphml(nom_fichier)
        if bavard: print("Graphe en mémoire !")
    else:
        print("Création du graphe via osmnx.")
        gr = crée_graphe_bbox(nom_fichier, bbox, bavard=bavard)
    g=Graphe_nx(gr)


    ## ville de chaque nœud. Va être nécessaire pour récupérer les nœuds des rues.
    if aussi_nœuds_des_villes:
        # Ville de chaque nœud
        print("\n\nRecherche de la liste des nœuds de chaque ville.")
        sauv_fichier(CHEMIN_NŒUDS_VILLES)
        csv_nœuds_des_villes(g)
    print(f"Création du csv villes_of_nœud")
    crée_csv_villes_of_nœuds(g,bavard=bavard)
    print("Ajout des villes de chaque nœud dans le graphe.")
    ajoute_villes(g, bavard=bavard)


    ## Nœuds de chaque rue
    print("\n\nCréation de la liste des nœuds de chaque rue.")
    sauv_fichier(CHEMIN_NŒUDS_RUES)
    csv_nœud_des_rues(g, bavard=bavard-1)

    ## Arbres lex des rues
    print("\nArbres lexicographiques des rues")
    créationArbre()
    
    return g


def rajoute_donnée(bbox=BBOX_DÉFAUT, garder_le_osm_complet=True):
    """
    NB : maintenant que rue_num_coords n’est plus utilisé, cette fonction devient inutile.

    Entrée : une bbox suffisamment petite pour être acceptée par overpass.
    Effet : récupère le .osm correspondant à la bounding box indiquée, et l’utilise pour compléter les données suivantes :
        - rue_num_coords (CHEMIN_RUE_NUM_COORDS)

    Paramètres:
       - garder_le_osm_complet : mettre à False pour forcer le retéléchargement  d’un fichier déjà présent.
    """

    print("J’essaie de télécharger le fichier .osm complet de la zone {bbox}, pour en extraire les coordonnées des numéros de rue disponibles. Sans cette étape, l’appli fonctionnera quand même, mais les numéros de rue seront ignorés.")
    chemin_osm_complet = os.path.join(TMP, str(bbox)+"_complet.osm")
    if garder_le_osm_complet and os.path.exists(chemin_osm_complet):
        print(f"Le fichier {chemin_osm_complet} est déjà présent, je le garde. Mettre le paramètre « garder_le_osm_complet » à False pour forcer le retéléchargement des données.")
    else:
        print("Téléchargement du fichier .osm complet.")
        
        lien = f"https://overpass.openstreetmap.ru/cgi/xapi_meta?*[bbox={o},{s},{n},{e}]"
        if bavard>0:print(lien)
        subprocess.run(["wget", "-O", chemin_osm_complet, lien])


    print("Recherche des coordonnées des numéros de rues disponibles. Au passage, servira pour la liste des villes.")
    sauv_fichier(CHEMIN_RUE_NUM_COORDS)
    extrait_rue_num_coords(chemin=chemin_osm_complet, bavard=1)


if __name__ == "__main__":
    initialisation_sans_overpass()
    rajoute_donnée()
