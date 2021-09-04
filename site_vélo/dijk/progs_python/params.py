# -*- coding:utf-8 -*-

from datetime import datetime
import os
import sys
sys.path.append("dijk/progs_python")
sys.path.append("dijk/")

RACINE_PROJET="dijk/progs_python/"


CHEMIN_XML = os.path.join(RACINE_PROJET, "données/voies_et_nœuds.osm")  #Adresse du fichier .osm élagué utilisé pour chercher les nœuds d'une rue.

CHEMIN_XML_COMPLET = os.path.join(RACINE_PROJET,"données_inutiles/pau_agglo.osm")
CHEMIN_JSON_NUM_COORDS = os.path.join(RACINE_PROJET,"données/rue_num_coords.csv")
CHEMIN_NŒUDS_VILLES = os.path.join(RACINE_PROJET,"données/nœuds_villes.csv")
CHEMIN_NŒUDS_RUES = os.path.join(RACINE_PROJET,"données/nœuds_rues.csv")
CHEMIN_CACHE = os.path.join(RACINE_PROJET,"données/cache_adresses.csv")
CHEMIN_CYCLA = os.path.join(RACINE_PROJET,"données/Cyclabilité.csv")
CHEMIN_CHEMINS = os.path.join(RACINE_PROJET,"données/chemins.csv")
DONNÉES = os.path.join(RACINE_PROJET,"données")

TMP = os.path.join(RACINE_PROJET, "tmp/")
os.makedirs(TMP, exist_ok=True)

STR_VILLE_DÉFAUT = "64000 Pau"  #Lorsque la ville n'est pas précisée par l'utilisateur
NAVIGATEUR = "firefox"  # Commande à lancer pour afficher les cartes html

D_MAX_POUR_NŒUD_LE_PLUS_PROCHE = 500 #en mètres


os.makedirs(os.path.join(RACINE_PROJET, "log"), exist_ok=True)
def LOG_PB(msg):
    f = open(os.path.join(RACINE_PROJET,"log/pb.log"), "a")
    f.write(f"{datetime.now()}   {msg}\n")
    f.close()
    print(msg)
LOG_PB("nouveau chargement de params.py\n\n")
