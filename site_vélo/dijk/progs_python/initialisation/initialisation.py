#!/usr/bin/python3
# -*- coding:utf-8 -*-

import os
import shutil
import subprocess

try:
    os.chdir("site_vélo/dijk/progs_python/")
except FileNotFoundError :
    print(f"Dossier actuel: {os.getcwd()}")

from params import TMP, CHEMIN_RUE_NUM_COORDS, CHEMIN_NŒUDS_VILLES, CHEMIN_NŒUDS_RUES
from initialisation.crée_graphe import crée_graphe_bbox
from initialisation.élaguage import élague_xml
from initialisation.numéros_rues import extrait_rue_num_coords
from initialisation.nœuds_des_rues import sortie_csv as csv_nœud_des_rues
from initialisation.ajoute_villes import crée_csv as csv_nœuds_des_villes
from module_graphe import graphe
from datetime import datetime

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
# list des villes : utiliser overpass cette fois ?

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


def initialisation_sans_overpass(bbox=(-0.45, 43.2671, -0.2541, 43.3403), bavard=1):
    """
    Entrée : bbox : (o, s, e, n) bounding box de la zone de laquelle récupérer les données.
    
    Effet :
       initialise les données qui ne nécessitent pas un gros téléchargement depuis openstreetmap mais qui passent uniquement par osmnx.
       rema : Il faudra que je voie comment s’y prend osmnx !

       Précisément, cette procédure crée :
             - le graphe au format graphml
             - rue_num_coords.csv (CHEMIN_RUE_NUM_COORDS) qui permet de retrouver les coords gps d’un numéro de rue
             - nœuds_rues.csv (CHEMIN_NŒUDS_RUES) qui donne les nœuds de chaque rue 
             - nœuds_ville.csv (CHEMIN_NŒUDS_VILLES) qui donne les nœuds de chaque ville

    """

    (o, s, e, n)=bbox
    
    print("Création du graphe via osmnx.")
    g = graphe(crée_graphe_bbox(f'{DONNÉES}/{o}{s}{e}{n}.graphml', ouest=o, est=e, nord=n, sud=s))

    print("Création de la liste des nœuds de chaque rue.")
    sauv_fichier(CHEMIN_NŒUDS_RUES)
    csv_nœud_des_rues(g)

    
    #print("Création de la liste des nœuds de chaque ville.")
    #sauv_fichier(CHEMIN_NŒUDS_VILLES)
    #csv_nœuds_des_villes()




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
