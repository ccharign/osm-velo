# -*- coding:utf-8 -*-
import time

from django.db.transaction import atomic
from django.db import close_old_connections

from dijk.progs_python.recup_donnees import récup_amenities
from dijk.models import TypeAmenity, Amenity, Zone

from params import LOG


#@atomic
def charge_type_amenities(ld):
    """
    ld (liste de dico), contient le résultat d’un récup_amenities
    Effet : remplit la table TypeAmenity avec les nouveaux. Demande interactivement la traduction en français.
    """

    déjà_présente = set((x[0] for x in TypeAmenity.objects.values_list("nom_osm")))

    for r in ld:
        if r["type"] in déjà_présente:
            # mise à jour ?
            #ta = TypeAmenity.objects.get(nom_osm = r["name"])
            None
        else:
            ta = TypeAmenity(nom_osm=r["type"])
            nom_traduit = input(f"Traduction de {r['type']} ? C’est pour {r['name']}. ")
            ta.nom_français = nom_traduit
            déjà_présente.add(r["type"])
            ta.save()
            if not nom_traduit:
                print(f"J’ignorerai à l’avenir le type {r['type']}")


def charge_amenities(ld, v_d, force=False):
    """
    ld (liste de dicos) : résultat de récup_amenities
    v_d (instance de Ville)
    params:
        force: si vrai, remplace celles déjà présentes dans la base.
    """
    déjà_présentes = set(x[0] for x in Amenity.objects.values_list("id_osm"))
    types_ignorés = set(x[0] for x in TypeAmenity.objects.filter(nom_français="").values_list("nom_osm"))
    
    for r in ld:
        if r["id_osm"] not in déjà_présentes and r["type"] not in types_ignorés:
            déjà_présentes.add(r["id_osm"])
            try:
                am = Amenity.of_dico(r, v_d)
                am.save()
            except RuntimeError as e:
                print(e)
            except django.db.utils.IntegrityError as e:
                print(r)
                print(déjà_présentes)
                print(e)
                
        elif force and r["id_osm"] in déjà_présentes:
            # Remplacer l’ancienne
            vieille = Amenity.objects.get(id_osm=r["id_osm"])
            vieille.delete()
            am = Amenity.of_dico(r, v_d)
            am.save()


def amenities_of_ville(v_d, bavard=0, force=False):
    """
    Récupère sur osm toutes les amenities (et shops) de la ville, et remplit les tables TypeAmenity et Amenity avec.
    params:
        - force : si True, remplace les amenities déjà présentes.
    """

    LOG(f"Amenities de {v_d}", bavard=1)
    LOG("Récupération des données via overpass", bavard=1)
    ld = récup_amenities(v_d)

    close_old_connections()
    LOG("Remplissage de la table des typesAmenity", bavard=1)
    charge_type_amenities(ld)
    
    LOG("Remplissage de la table Amenity", bavard=1)
    charge_amenities(ld, v_d, force=force)


def amenities_of_zone(z_t, force=False):
    z_d = Zone.objects.get(nom=z_t)
    for rel in z_d.ville_zone_set.all():
        amenities_of_ville(rel.ville, force=force)
        print("Pause de 10s pour overpass")
        time.sleep(10)
