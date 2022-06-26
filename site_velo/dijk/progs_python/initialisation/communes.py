# -*- coding:utf-8 -*-

import os
import json
from functools import reduce

from django.db import transaction, close_old_connections

from dijk.models import Ville

from dijk.progs_python.lecture_adresse.normalisation import normalise_ville, normalise_rue, prétraitement_rue, partie_commune

from params import RACINE_PROJET


### Données INSEE ###


def int_of_code_insee(c):
    """
    Entrée : (str) code INSEE
    Sortie (int) : entier obtenu en remplaçant A par 00 et B par 01 ( à cause de la Corse) et en convertissant le résultat en int.
    """
    return int(c.replace("A","00").replace("B","01"))


def charge_villes(chemin_pop=os.path.join(RACINE_PROJET, "progs_python/stats/docs/densité_communes.csv"),
                  chemin_géom=os.path.join(RACINE_PROJET, "progs_python/stats/docs/géom_villes.json"),
                  bavard=0 ):
    """
    Remplit la table des villes à l’aide des deux fichiers insee. (Il manque le code postal.)
    """
    
    dico_densité={"Communes très peu denses":0,
                  "Communes peu denses":1,
                  "Communes de densité intermédiaire":2,
                  "Communes densément peuplées":3
                  }

    def géom_vers_texte(g):
        """
        Enlève d’éventuelles paires de crochets inutiles avant de tout convertir en une chaîne de (lon, lat) séparées par des ;.
        """
        assert isinstance(g, list), f"{g} n’est pas une liste"
        if len(g)==1:
            return géom_vers_texte(g[0])
        elif isinstance(g[0][0], list):
            nv_g = reduce(lambda x,y : x+y, g, [])
            return géom_vers_texte(nv_g)
        else:
            assert len(g[0])==2, f"{g} n’est pas une liste de couples.\n Sa longueur est {len(g)}"
            return ";".join(map(
                lambda c: ",".join(map(str, c)),
                g
            ))

    dico_géom = {} # dico code_insee -> (nom, géom)

    print(f"Lecture de {chemin_géom} ")
    with open(chemin_géom) as entrée:
        données = json.load(entrée)
        for v in données["features"]:
            code_insee = int_of_code_insee(v["properties"]["codgeo"])
            géom = géom_vers_texte(v["geometry"]["coordinates"])
            nom = v["properties"]["libgeo"].strip().replace("?","'")
            dico_géom[code_insee] = (nom, géom)
    

    print(f"Lecture de {chemin_pop}")
    close_old_connections()
    with transaction.atomic():
        with open(chemin_pop) as entrée:
            à_maj=[]
            à_créer=[]
            n=-1
            entrée.readline()
            for ligne in entrée:
                n+=1
                if n % 500 ==0: print(f"{n} lignes traitées")
                code_insee, nom, région, densité, population = ligne.strip().split(";")
                code_insee = int_of_code_insee(code_insee)
                population = int(population.replace(" ",""))
                i_densité = dico_densité[densité]
                essai = Ville.objects.filter(nom_complet=nom).first()
                if code_insee in dico_géom:
                    nom_dans_géom, géom = dico_géom[code_insee]
                    if nom!=nom_dans_géom:
                        print(f"Avertissement : nom différent dans les deux fichiers : {nom_dans_géom} et {nom}")
                        géom=None
                else:
                    print(f"Avertissement : ville pas présente dans {chemin_géom} : {nom}")
                    géom = None

                if essai:
                    essai.population=population
                    essai.code_insee=code_insee
                    essai.densité=i_densité
                    essai.géom_texte = géom
                    à_maj.append(essai)
                else:
                    v_d = Ville(nom_complet=nom,
                                nom_norm=partie_commune(nom),
                                population=population,
                                code_insee=code_insee,
                                code=None,
                                densité=i_densité,
                                géom_texte=géom
                                )
                    à_créer.append(v_d)
    print(f"Enregistrement des {len(à_maj)} modifs")
    Ville.objects.bulk_update(à_maj, ["population", "code_insee", "densité"])
    print(f"Enregistrement des {len(à_créer)} nouvelles villes")
    Ville.objects.bulk_create(à_créer)



@transaction.atomic()
def renormalise_noms_villes():
    """
    Effet : recalcule le champ nom_norm de chaque ville au moyen de partie_commune.
    Utile si on changé cette dernière fonction.
    """
    n=0
    for v in Ville.objects.all():
        if n%500==0: print(f"{n} communes traitées")
        n+=1
        v.nom_norm = partie_commune(v.nom_complet)
        v.save()
        

def charge_géom_villes(chemin=os.path.join(RACINE_PROJET, "progs_python/stats/docs/géom_villes.json")):
    """
    Rajoute la géométrie des villes à partir du json INSEE.
    """
    

        
    with open(chemin) as entrée:
        à_maj=[]
        
    Ville.objects.bulk_update(à_maj, ["géom_texte"])


def ajoute_villes_voisines():
    """
    Remplit les relations ville-ville dans la base.
    """
    dico_coords = {} # dico coord -> liste de villes
    à_ajouter=[]
    print("Recherche des voisinages")
    for v in Ville.objects.all():
        for c in v.géom_texte.split(";"):
            if c in dico_coords:
                for v2 in dico_coords[c]:
                    à_ajouter.append(Ville_Ville(ville1=v, ville2=v2))
                    à_ajouter.append(Ville_Ville(ville1=v2, ville2=v))
                    dico_coords[c].append(v)
            else:
                dico_coords[c] = [v]
    print("Élimination des relations déjà présente")
    à_ajouter_vraiment=[]
    for r in à_ajouter:
        if not Ville_Ville.objects.filter(ville1=r.ville1, ville2=r.ville2).exists():
            à_ajouter_vraiment.append(r)
    print("Enregistrement")
    Ville_Ville.objects.bulk_create(à_ajouter_vraiment)
