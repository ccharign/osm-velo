# -*- coding:utf-8 -*-

from datetime import datetime
CHEMIN_XML = "données/voies_et_nœuds.osm" #Adresse du fichier .osm élagué utilisé pour chercher les nœuds d'une rue.
VILLE_DÉFAUT = "64000 Pau" #Lorsque la ville n'est pas précisée par l'utilisateur
CHEMIN_XML_COMPLET = "données_inutiles/pau_agglo.osm"

def LOG_PB(msg):
    f = open("log/pb.log", "a")
    f.write(f"{datetime.now()}   {msg}\n")
    f.close()
    print(msg)
