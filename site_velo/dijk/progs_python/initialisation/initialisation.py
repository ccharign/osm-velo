#!/usr/bin/python3
# -*- coding:utf-8 -*-

import os
import subprocess

# if os.getcwd()=="/home/moi/git/osm vélo":
#     os.chdir("site_velo/")
# else :
#     print(f"Dossier actuel: {os.getcwd()}")
    
import osmnx

from time import perf_counter
from dijk.progs_python.params import TMP, CHEMIN_RUE_NUM_COORDS, CHEMIN_NŒUDS_VILLES, CHEMIN_NŒUDS_RUES, DONNÉES, BBOX_DÉFAUT
from initialisation.crée_graphe import crée_graphe_bbox
#from initialisation.élaguage import élague_xml
from initialisation.numéros_rues import extrait_rue_num_coords
from initialisation.noeuds_des_rues import sortie_csv as csv_nœud_des_rues, extrait_nœuds_des_rues
from initialisation.ajoute_villes import crée_csv as csv_nœuds_des_villes, ajoute_villes, crée_csv_villes_of_nœuds
from lecture_adresse.normalisation import créationArbre, arbre_rue_dune_ville, partie_commune
from graphe_par_networkx import Graphe_nx
from petites_fonctions import sauv_fichier, chrono
#from networkx import read_graphml
from dijk.models import Ville, Zone, Cache_Adresse, Ville_Zone, Sommet
from django.db import close_old_connections
import initialisation.vers_django as vd
from utils import lecture_tous_les_chemins

"""
Script pour réinitialiser ou ajouter une nouvelle zone.

Ce scrit ne réinitialise *pas* le cache ni la cyclabilité.
   -> À voir, peut être le cache ?
   -> Ou carrément recréer le cache...
"""



def charge_ville(nom, code, zone="Pau_agglo", ville_defaut=None, pays="France", bavard=2):
    """
    Entrées : nom (str)
              code (int)
              zone (str)
    Effet : 
        Charge les données osm de la ville dans la base, à savoir:
           - Sommets
           - Arêtes
           - Rues
        Le tout associé à la zone indiquée, qui est créée si besoin.
        Le code postal est rajouté à la base s’il n’y était pas.
    """


    ## Création ou récupération de la zone
    if ville_defaut is not None:
        zone_d, créée = Zone.objects.get_or_create(nom=zone, ville_défaut=Ville.objects.get(nom_complet=ville_defaut))
        if créée:
            zone_d.save()
    else:
        zone_d = Zone.objects.get(nom=zone)

        
    ## Ville : ajout du code postal et de la zone
    ville_d = vd.ajoute_code_postal(nom, code)
    rel, créée = Ville_Zone.objects.get_or_create(ville=ville_d, zone=zone_d)
    if créée: rel.save()

    
    ## Récup des graphe via osmnx
    print(f"Récupération du graphe pour « {ville_d.code} {ville_d.nom_complet}, {pays} » avec une marge")
    gr_avec_marge = osmnx.graph_from_place(
        {"city":f"{ville_d.nom_complet}", "postcode":ville_d.code, "country":pays},
        network_type="all", # Tout sauf private
        retain_all="False", # Sinon il peut y avoir des enclaves déconnectées car accessibles seulement par chemin privé (ex: CSTJF)
        buffer_dist=500  # Marge de 500m
    )
    print("\nRécupération du graphe exact")
    gr_strict = osmnx.graph_from_place({"city":f"{nom}", "postcode":code, "country":pays}, network_type="all", retain_all="True")

    g = Graphe_nx(gr_avec_marge)
    
    ## Noms des villes
    print("\nAjout du nom de ville.")
    for n in gr_strict.nodes:
        #if n not in g.villes_of_nœud: g.villes_of_nœud=[]
        g.villes_of_nœud[n] = [nom]

    ## nœuds des rues
    print("\nCalcul des nœuds de chaque rue")
    dico_rues = extrait_nœuds_des_rues(g, bavard=bavard-1) # dico ville -> rue -> liste nœuds # Seules les rues avec nom de ville, donc dans g_strict seront calculées.
    print("Écriture des nœuds des rues dans la base.")
    close_old_connections()
    vd.charge_dico_rues_nœuds(ville_d, dico_rues[nom])
    print("Création de l'arbre lexicographique")
    arbre_rue_dune_ville(ville_d,
                         map(partie_commune, dico_rues[nom].keys())
                         )

    ## désorientation
    print("\nDésorientation du graphe")
    vd.désoriente(g, bavard=bavard-1)
    
    ## Transfert du graphe
    vd.transfert_graphe(g, zone_d, bavard=bavard-1, juste_arêtes=False)

    
    ville_d.données_présentes = True
    ville_d.save()
    

À_RAJOUTER_PAU={
    "Gelos": 64110,
    "Lée": 64320,
    "Pau": 64000,
    "Lescar": 64230,
    "Billère": 64140,
    "Jurançon": 64110,
    "Ousse": 64320,
    "Idron": 64320,
    "Lons": 64140 ,
    "Bizanos": 64320,
    "Artigueloutan": 64420,
    "Mazères-Lezons": 64110
}.items()


def charge_zone(liste_villes=À_RAJOUTER_PAU, réinit=False, zone="Pau_agglo", ville_defaut="Pau", bavard=2):
    """
    Entrée : liste_villes, itérable de (nom de ville, code postal)
             zone (str), nom de la zone
             ville_defaut (str), nom de la ville par défaut de la zone. Utilisé uniquement si la zone est créée.

    Effet : charge toutes ces ville dans la base, associées à la zone indiquée.
            Si la zone n’existe pas, elle sera créée, en y associant ville_défaut.

    Paramètres: 
       Si réinit, tous les éléments associés à la zone (villes, rues, sommets, arêtes) ainsi que le cache sont au préalable supprimés.
    """

    ## Récupération ou création de la zone :
    zs_d = Zone.objects.filter(nom=zone)
    if zs_d.exists():
        z_d=zs_d.first()
    else:
        ville_défaut_d = Ville.objects.get(nom_complet=ville_defaut)
        #ville_défaut_d, _ = Ville.objects.get_or_create(nom_complet=ville_défaut, code=code, nom_norm=partie_commune(ville_défaut))
        z_d = Zone(nom=zone, ville_défaut=ville_défaut_d)
        z_d.save()

    ## Réinitialisation de la zone :
    if réinit:         
        for v in z_d.villes():
            v.delete()
        Sommet.objects.filter(zone=z_d).delete()
        Cache_Adresse.objects.all().delete()

    ## Chargement des villes :
    for nom, code in liste_villes:
        charge_ville(nom, code, zone=zone, bavard=bavard)



def init_totale():
    
    print("Chargement des villes depuis les fichiers INSEE")
    vd.charge_villes()
 
    print("Chargement des données osm")
    charge_zone()
    



def charge_multidigraph():
    """
    Renvoie le multidigraph de la zone défaut. Plutôt pour tests.
    """
    s,o,n,e = BBOX_DÉFAUT
    nom_fichier = f'{DONNÉES}/{s}{o}{n}{e}.graphml'
    g = osmnx.load_graphml(nom_fichier)
    return g
