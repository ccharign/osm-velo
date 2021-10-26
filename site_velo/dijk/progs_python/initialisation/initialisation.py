#!/usr/bin/python3
# -*- coding:utf-8 -*-

import os
import shutil
import subprocess
from datetime import datetime

if os.getcwd()=="/home/moi/git/osm vélo":
    os.chdir("site_vélo/")
else :
    print(f"Dossier actuel: {os.getcwd()}")
    
import osmnx.io

from dijk.progs_python.params import TMP, CHEMIN_RUE_NUM_COORDS, CHEMIN_NŒUDS_VILLES, CHEMIN_NŒUDS_RUES, DONNÉES, BBOX_DÉFAUT
from initialisation.crée_graphe import crée_graphe_bbox
from initialisation.élaguage import élague_xml
from initialisation.numéros_rues import extrait_rue_num_coords
from initialisation.nœuds_des_rues import sortie_csv as csv_nœud_des_rues
from initialisation.ajoute_villes import crée_csv as csv_nœuds_des_villes, ajoute_villes
from graphe_minimal import Graphe_minimaliste


"""
Script pour tout initialiser, càd:
    -- le graphe au format graphml
    -- les différents fichiers du graphe, à savoir dans l’ordre:
             - la carte .osm complète (CHEMIN_XML_COMPLET)
             - la carte élaguée (CHEMIN_XML)
             - rue_num_coords.csv (CHEMIN_RUE_NUM_COORDS) qui permet de retrouver les coords gps d’un numéro de rue
             - nœuds_rues.csv (CHEMIN_NŒUDS_RUES) qui donne les nœuds de chaque rue 
             - nœuds_ville.csv (CHEMIN_NŒUDS_VILLES) qui donne les nœuds de chaque ville 


Ce scrit ne réinitialise *pas* le cache ni la cyclabilité.
   -> À voir, peut être le cache ?
   -> Ou carrément recréer le cache...
Il ne crée aucun objet Python, seulement des fichiers : peut être utilisé indépendemment du reste.
   -> le paramétrer pour usage en script
"""


## À FAIRE :
# Quid du fichier osm élaguée ? Peut-on le tirer directement du graphe networkx ? Peut-on s’en passer entièrement ?
# liste des villes : utiliser overpass cette fois ?

def sauv_fichier(chemin):
    """
    Crée une copie du fichier dans le sous-répertoire « sauv » du répertoire contenant le fichier. Le sous-répertoire « sauv » doit exister au préalable.
    """
    dossier, nom = os.path.split(chemin)
    dossier_sauv = os.path.join(dossier,"sauv")
    os.makedirs(dossier_sauv, exist_ok=True)
    nom_sauv = nom+str(datetime.now())
    shutil.copyfile(
        chemin,
        os.path.join(dossier_sauv, nom_sauv)
    )


def initialisation_sans_overpass(bbox=BBOX_DÉFAUT, bavard=1):
    """
    Entrée : bbox : (o, s, e, n) bounding box de la zone de laquelle récupérer les données.
    
    Effet :
       Initialise les données qui ne nécessitent pas un gros téléchargement depuis openstreetmap mais qui passent uniquement par osmnx.
       rema : Il faudra voir comment s’y prend osmnx !

       Précisément, cette procédure crée :
             - le graphe au format graphml
             - nœuds_ville.csv (CHEMIN_NŒUDS_VILLES) qui donne les nœuds de chaque ville
             - nœuds_rues.csv (CHEMIN_NŒUDS_RUES) qui donne les nœuds de chaque rue
    """

    (o, s, e, n) = bbox
    nom_fichier=f'{DONNÉES}/{o}{s}{e}{n}.graphml'
    try:
        gr = osmnx.io.load_graphml(nom_fichier)
        if bavard: print("Graphe en mémoire !")
    except FileNotFoundError:
        print("Création du graphe via osmnx.")
        gr = crée_graphe_bbox(nom_fichier, ouest=o, est=e, nord=n, sud=s)
    g=Graphe_minimaliste(gr)
    
    #print("Création de la liste des nœuds de chaque ville.")
    #sauv_fichier(CHEMIN_NŒUDS_VILLES)
    #csv_nœuds_des_villes()
    
    print("Ajout des villes dans le graphe")
    ajoute_villes(g)
    
    print("Création de la liste des nœuds de chaque rue.")
    sauv_fichier(CHEMIN_NŒUDS_RUES)
    csv_nœud_des_rues(g)

    return g


def rajoute_donnée(bbox, garder_le_osm_complet=True):
    """
    Entrée : une bbox suffisamment petite pour être acceptée par overpass.
    Effet : récupère le .osm correspondant à la bounding box indiquée, et l’utilise pour compléter les données suivantes :
        - rue_nom_coords (CHEMIN_RUE_NUM_COORDS)

    Paramètres:
       - garder_le_osm_complet : mettre à False pour forcer le retéléchargement  d’un fichier déjà présent.
    """


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
