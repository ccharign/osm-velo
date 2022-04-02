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
from lecture_adresse.normalisation import créationArbre, arbre_rue_dune_ville, partie_commune, prétraitement_rue, normalise_rue
from graphe_par_networkx import Graphe_nx
from petites_fonctions import sauv_fichier, chrono, union
#from networkx import read_graphml
from dijk.models import Ville, Zone, Cache_Adresse, Ville_Zone, Sommet, Rue, Arête
from django.db import close_old_connections, transaction
import initialisation.vers_django as vd
from utils import lecture_tous_les_chemins
from params import RACINE_PROJET

"""
Script pour réinitialiser ou ajouter une nouvelle zone.

Ce scrit ne réinitialise *pas* le cache ni la cyclabilité.
   -> À voir, peut être le cache ?
   -> Ou carrément recréer le cache...
"""



def charge_ville(nom, code, zone, ville_defaut=None, pays="France", bavard=2, rapide = 0):
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
    Paramètres:
        - rapide (int) : indique la stratégie en cas de données déjà présentes.
             pour tout  (s,t) sommets voisins dans g,
                0 -> efface toutes les arêtes de s vers t et remplace par celles de g
                1 -> regarde si les arête entre s et t dans g correspondent à celles dans la base, et dans ce cas ne rien faire.
                        « correspondent » signifie : même nombre et mêmes noms.
                2 -> si il y a quelque chose dans la base pour (s,t), ne rien faire.
    """


    ## Création ou récupération de la zone
    if ville_defaut is not None:
        zone_d, créée = Zone.objects.get_or_create(nom=zone, ville_défaut=Ville.objects.get(nom_norm= partie_commune( ville_defaut)))
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

        
    ## Nœuds des rues
    print("\nCalcul des nœuds de chaque rue")
    dico_rues = extrait_nœuds_des_rues(g, bavard=bavard-1) # dico ville -> rue_n -> (rue, liste nœuds) # Seules les rues avec nom de ville, donc dans g_strict seront calculées.
    print("Écriture des nœuds des rues dans la base.")
    close_old_connections()
    vd.charge_dico_rues_nœuds(ville_d, dico_rues[nom])
    
    print("Création de l'arbre lexicographique")
    arbre_rue_dune_ville(
        ville_d,
        dico_rues[nom].keys()
    )

    ## Désorientation
    close_old_connections()
    print("\nDésorientation du graphe")
    vd.désoriente(g, bavard=bavard-1)
    
    ## Transfert du graphe
    close_old_connections()
    arêtes_créées, arêtes_màj = vd.transfert_graphe(g, zone_d, bavard=bavard-1, juste_arêtes=False, rapide=rapide)

    # Ajout de la ville aux arêtes
    # print("Ajout de la ville aux arêtes")
    # rel_àcréer=[]
    # for a_d in union(arêtes_màj, arêtes_créées):
    #     if a_d.départ.id_osm in gr_strict and a_d.arrivée.id_osm in gr_strict:
    #         if ville_d not in a_d.ville.all():
    #             rel_àcréer.append(Arête.ville.through(arête_id=a_d.id, ville_id=ville_d.id))
    # print("  bulk_create")
    # Arête.ville.through.bulk_create(rel_àcréer)
    # print("  fini")
    
    ville_d.données_présentes = True
    ville_d.save()
    

def crée_tous_les_arbres_des_rues():
    """
    Effet : crée tous les arbres lexicographiques des rues des villes qui appartiennent à au moins une zone, en repartant du nom complet présent dans la base.
    """

    dico_arbres = {} # dico id_ville -> liste des rues
    for id_v, in Ville_Zone.objects.values_list("ville_id").distinct():
        dico_arbres[id_v] = []

    for nom_rue, id_v in Rue.objects.values_list("nom_complet", "ville_id"):
        dico_arbres[id_v].append(nom_rue)
    for id_v, l in dico_arbres.items():
        ville_d = Ville.objects.get(pk=id_v)
        arbre_rue_dune_ville(
            ville_d,
            map(prétraitement_rue, l)
        )
    

    
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

ZONE_VOIRON={
    "saint étienne de crossey":38960,
    "coublevie":38500,
    "la buisse":38500,
    "saint aupre":38960,
    "voiron":38500
}.items()


def charge_zone(liste_villes=À_RAJOUTER_PAU, réinit=False, zone="Pau_agglo", ville_defaut="Pau", bavard=2, rapide=0):
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
        charge_ville(nom, code, zone, bavard=bavard, rapide=rapide)



def init_totale():
    
    print("Chargement des villes depuis les fichiers INSEE")
    vd.charge_villes()
 
    print("Chargement des données osm")
    charge_zone()
    



def charge_multidigraph():
    """
    Renvoie le multidigraph de la zone défaut, supposé enregistré sur le disque. Plutôt pour tests.
    """
    s,o,n,e = BBOX_DÉFAUT
    nom_fichier = f'{DONNÉES}/{s}{o}{n}{e}.graphml'
    g = osmnx.load_graphml(nom_fichier)
    return g


def charge_fichier_cycla_défaut(g, chemin=os.path.join(RACINE_PROJET, "progs_python/initialisation/données/rues et cyclabilité.txt"), zone="Pau_agglo"):
    """
    Entrées : g (graphe)
              chemin (str)
    Effet : remplit la cycla_défaut des rues indiquées dans le fichier.
    
    """
    z_d = Zone.objects.get(nom=zone)
    with transaction.atomic():
        with open(chemin) as entrée:
            for ligne in entrée:
                if ligne[:6]=="cycla ":
                    cycla = 1.1**int(ligne[6:].strip())
                    print(f"\n\nRues de cyclabilité {cycla}")
                elif ligne.strip()=="":
                    None
                elif ligne[:2]=="à ":
                    v_d = Ville.objects.get(nom_norm = partie_commune(ligne[2:].strip().replace(":","")))
                    print(f"\n  Ville {v_d}")
                else:
                    nom_n, nom_osm,_ = normalise_rue(g, z_d, ligne.strip(), v_d)
                    print(f"    {nom_osm}")
                    rue = Rue.objects.get(nom_norm=nom_n, ville=v_d)
                    sommets = frozenset(g.dico_Sommet[s] for s in  rue.nœuds())
                    for s in sommets:
                        for a in Arête.objects.filter(départ=s).select_related("arrivée"):
                            if a.arrivée in sommets:
                                if abs(a.cycla_défaut)< abs(cycla):
                                    print(f"À mettre à jour : ancienne cycla_défaut {a.cycla_défaut}")
                                    a.cycla_défaut=cycla
                                    a.save()
