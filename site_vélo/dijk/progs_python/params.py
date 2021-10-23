# -*- coding:utf-8 -*-

from datetime import datetime
import os
import sys
sys.path.append("dijk/progs_python")
sys.path.append("dijk/")



### Adresses des fichiers de données ###

RACINE_PROJET="dijk/"

DONNÉES = os.path.join(RACINE_PROJET,"données/Pau")
TMP = os.path.join(RACINE_PROJET, "tmp/")
os.makedirs(TMP, exist_ok=True)
os.makedirs(DONNÉES, exist_ok=True)

CHEMIN_XML = os.path.join(DONNÉES, "voies_et_nœuds.osm")  #Adresse du fichier .osm élagué utilisé pour chercher les nœuds d'une rue.
CHEMIN_XML_COMPLET = os.path.join(TMP,"pau_agglo.osm") # le .osm complet. Mis dans TMP pour ne pas être transféré sur github
CHEMIN_RUE_NUM_COORDS = os.path.join(DONNÉES,"rue_num_coords.csv")
CHEMIN_NŒUDS_VILLES = os.path.join(DONNÉES,"nœuds_villes.csv")
CHEMIN_NŒUDS_RUES = os.path.join(DONNÉES,"nœuds_rues.csv")
CHEMIN_CACHE = os.path.join(DONNÉES,"cache_adresses.csv")
CHEMIN_CYCLA = os.path.join(DONNÉES,"Cyclabilité.csv")
CHEMIN_CHEMINS = os.path.join(DONNÉES,"chemins.csv")



### Réglages divers ###

STR_VILLE_DÉFAUT = "64000 Pau"  #Lorsque la ville n'est pas précisée par l'utilisateur
PAYS_DÉFAUT = "France"
#NAVIGATEUR = "firefox"  # Commande à lancer pour afficher les cartes html # Plus utilisé : utilisation de la commande Python idoine à la place à savoir webbrowser

D_MAX_POUR_NŒUD_LE_PLUS_PROCHE = 500 #en mètres


### logs ###
os.makedirs(os.path.join(RACINE_PROJET, "log"), exist_ok=True)
def LOG_PB(msg):
    f = open(os.path.join(RACINE_PROJET,"log/pb.log"), "a")
    f.write(f"{datetime.now()}   {msg}\n")
    f.close()
    print(msg)
LOG_PB("Nouveau chargement de params.py\n\n")
