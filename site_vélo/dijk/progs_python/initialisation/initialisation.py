# -*- coding:utf-8 -*-
import os
import shutil
from crée_graphe.py import crée_graphe_bbox

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
Il ne crée aucun objet Python, seulement des fichiers.
"""


def sauv_fichier(chemin):
    """
    Crée une copie du fichier dans le sous-répertoire « sauv » du répertoire contenant le fichier. Le sous-répertoire « sauv » doit exister au préalable.
    """
    dossier, nom = os.path.split(chemin)
    shutil.copyfile(
        chemin,
        os.path.join(os.path.join(dossier,"sauv"), nom)
    )


def initialisation(bbox, bavard=0):
    """
    Entrée : bbox : (o, s, e, n) bounding box de la zone de laquelle récupérer les données.
    Effet : création
             - du graphe au format graphml
             - la carte .osm complète (CHEMIN_XML_COMPLET)
             - la carte élaguée (CHEMIN_XML)
             - rue_num_coords.csv (CHEMIN_RUE_NUM_COORDS) qui permet de retrouver les coords gps d’un numéro de rue
             - nœuds_rues.csv (CHEMIN_NŒUDS_RUES) qui donne les nœuds de chaque rue 
             - nœuds_ville.csv (CHEMIN_NŒUDS_VILLES) qui donne les nœuds de chaque ville
    """
    
    crée_graphe_bbox()
