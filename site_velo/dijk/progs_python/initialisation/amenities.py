# -*- coding:utf-8 -*-
import time

from django.db.transaction import atomic

from dijk.progs_python.recup_donnees import récup_amenities
from dijk.models import TypeAmenity, Amenity, Ville, Zone

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


@atomic
def charge_amenities(ld, v_d):
    """
    ld (liste de dicos) : résultat de récup_amenities
    liste_types (str set): ensembles des types pris en compte.
    v_d (instance de Ville)
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


def amenities_of_ville(v_d, bavard=0):
    """
    Récupère sur osm toutes les amenities (et shops) de la ville, et remplit les tables TypeAmenity et Amenity avec.
    """

    LOG(f"Amenities de {v_d}", bavard=1)
    LOG("Récupération des données via overpass", bavard=1)
    ld = récup_amenities(v_d)
    
    LOG("Remplissage de la table des typesAmenity", bavard=1)
    charge_type_amenities(ld)
    
    LOG("Remplissage de la table Amenity", bavard=1)
    charge_amenities(ld, v_d)


def amenities_of_zone(z_t):
    z_d= Zone.objects.get(nom=z_t)
    for rel in z_d.ville_zone_set.all():
        amenities_of_ville(rel.ville)
        print("Pause de 10s pour overpass")
        time.sleep(10)
