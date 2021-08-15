# -*- coding:utf-8 -*-

from datetime import datetime
import os.path

RACINE_PROJET="/home/moi/git/osm\ vélo"

CHEMIN_XML = os.path.join(RACINE_PROJET, "données/voies_et_nœuds.osm")  #Adresse du fichier .osm élagué utilisé pour chercher les nœuds d'une rue.

CHEMIN_XML_COMPLET = os.path.join(RACINE_PROJET,"données_inutiles/pau_agglo.osm")
CHEMIN_JSON_NUM_COORDS = os.path.join(RACINE_PROJET,"données/rue_num_coords.json")
CHEMIN_NŒUDS_VILLES = os.path.join(RACINE_PROJET,"données/nœuds_villes.csv")

VILLE_DÉFAUT = "64000 Pau"  #Lorsque la ville n'est pas précisée par l'utilisateur
NAVIGATEUR = "firefox"  # Commande à lancer pour afficher les cartes html


def LOG_PB(msg):
    f = open(os.path.join(RACINE_PROJET,"log/pb.log"), "a")
    f.write(f"{datetime.now()}   {msg}\n")
    f.close()
    print(msg)
