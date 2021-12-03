#!/usr/bin/python3
# -*- coding:utf-8 -*-

import os
import subprocess

if os.getcwd()=="/home/moi/git/osm vélo":
    os.chdir("site_velo/")
else :
    print(f"Dossier actuel: {os.getcwd()}")
    
import osmnx.io

from dijk.progs_python.params import TMP, CHEMIN_RUE_NUM_COORDS, CHEMIN_NŒUDS_VILLES, CHEMIN_NŒUDS_RUES, DONNÉES, BBOX_DÉFAUT
from initialisation.crée_graphe import crée_graphe_bbox
#from initialisation.élaguage import élague_xml
from initialisation.numéros_rues import extrait_rue_num_coords
from initialisation.noeuds_des_rues import sortie_csv as csv_nœud_des_rues
from initialisation.ajoute_villes import crée_csv as csv_nœuds_des_villes, ajoute_villes, crée_csv_villes_of_nœuds
from lecture_adresse.normalisation import créationArbre
from graphe_par_networkx import Graphe_nx
from petites_fonctions import sauv_fichier
#from networkx import read_graphml


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
   De toute façon le cache est assez peu utilisé me semble-t-il maintenant.

Il ne crée aucun objet Python, seulement des fichiers : peut être utilisé indépendemment du reste.
   -> le paramétrer pour usage en script

"""


## À FAIRE :
# Quid du fichier osm élaguée ? Peut-on le tirer directement du graphe networkx ? Peut-on s’en passer entièrement ?
# liste des villes : utiliser overpass cette fois ?




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
    
    if aussi_nœuds_des_villes:
        # Ville de chaque nœud
        print("\n\nRecherche de la liste des nœuds de chaque ville.")
        #if bavard>0:print("  Note : on pourrait ne garder que les nœuds de g...") # Maintenant c’est fait
        sauv_fichier(CHEMIN_NŒUDS_VILLES)
        csv_nœuds_des_villes(g)
    print(f"Création du csv villes_of_nœud")
    crée_csv_villes_of_nœuds(g,bavard=bavard)
    print("Ajout des villes de chaque nœud dans le graphe.")
    ajoute_villes(g, bavard=bavard)
    
    print("\n\nCréation de la liste des nœuds de chaque rue.")
    sauv_fichier(CHEMIN_NŒUDS_RUES)
    csv_nœud_des_rues(g, bavard=bavard-1)

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
