# -*- coding:utf-8 -*-

import time
tic0 = time.perf_counter()
from glob import glob
import os
import traceback
import json
import re

from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Subquery, Q

from dijk import forms

from .progs_python.params import LOG
from .progs_python.petites_fonctions import chrono

from .progs_python.chemins import Chemin, Étape, ÉtapeArête

from .progs_python.lecture_adresse.recup_noeuds import PasTrouvé
from .progs_python.lecture_adresse.normalisation0 import prétraitement_rue
from .progs_python import recup_donnees
from .progs_python.apprentissage import n_lectures, lecture_jusqu_à_perfection, lecture_plusieurs_chemins
from .progs_python.bib_vues import bool_of_checkbox, énumération_texte, sans_style, récup_head_body_script, récup_données, z_é_i_d


from .progs_python.utils import dessine_chemin, dessine_cycla, itinéraire_of_étapes


from .progs_python.graphe_par_django import Graphe_django
from .progs_python.lecture_adresse.normalisation0 import découpe_adresse

from .models import Chemin_d, Zone, Rue, Ville_Zone, Cache_Adresse, CacheNomRue, Amenity

chrono(tic0, "Chargement total\n\n", bavard=3)


g = Graphe_django()





#https://stackoverflow.com/questions/18176602/how-to-get-the-name-of-an-exception-that-was-caught-in-python
def get_full_class_name(obj):
    module = obj.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return obj.__class__.__name__
    return module + '.' + obj.__class__.__name__




def choix_zone(requête):
    """
    Page d’entrée du site. Formulaire de choix de zone.
    """
    if requête.method == "GET" and requête.GET:
        form = forms.ChoixZone(requête.GET)
        if form.is_valid():
            z_d = form.cleaned_data["zone"]
            return recherche(requête, z_d.nom)
    
    form = forms.ChoixZone()
    return render(requête, "dijk/index.html", {"form": form})


def fouine(requête):
    requête.session["fouine"] = True
    return choix_zone(requête)


def limitations(requête):
    return render(requête, "dijk/limitations.html", {})


def mode_demploi(requête):
    return render(requête, "dijk/mode_demploi.html", {})


def contribution(requête):
    return render(requête, "dijk/contribution.html", {})


def sous_le_capot(requête):
    return render(requête, "dijk/sous_le_capot.html", {})


# def visualisation_nv_chemin(requête):
#     return render(requête, "dijk/iti_folium.html", {})






### Formulaires de recherche d’itinéraire


def recherche(requête, zone_t):
    """
    Vue pour une recherche de base.
    """
    # données = dict_of_get(requête.GET)
    # form_zone = forms.ChoixZone(requête.GET)
    # if not form_zone.is_valid():
    #     print(form_zone.errors)
    # données.update(form_zone.cleaned_data)
    données = récup_données(requête.GET, forms.ChoixZone, validation_obligatoire=False)
    if "zone" in données and données["zone"]:
        z_d = g.charge_zone(données["zone"].nom)
        requête.session["zone"] = z_d.nom
        requête.session["zone_id"] = z_d.pk
    elif "zone" in requête.session:
        z_d = g.charge_zone(requête.session["zone"])
        données["zone"] = z_d
    else:
        return choix_zone(requête)
    
    if requête.GET and "arrivée" in requête.GET:
        form_recherche = forms.Recherche(données)
        if form_recherche.is_valid():
            données.update(form_recherche.cleaned_data)
            z_d, étapes, étapes_interdites, ps_détour = z_é_i_d(g, données)

            return calcul_itinéraires(requête, ps_détour, z_d,
                                      étapes,
                                      étapes_interdites=étapes_interdites,
                                      données=données,
                                      bavard=1
                                      )
        else:
            # form pas valide
            print(form_recherche.errors)
    else:
        form_recherche = forms.Recherche(initial=données)
    return render(requête, "dijk/recherche.html",
                  {"ville": z_d.ville_défaut, "zone_t": zone_t, "recherche": form_recherche}
                  )



def relance_rapide(requête):
    """
    Relance un calcul à partir du résultat du formulaire de relance rapide.
    Les étapes sont dans des champs dont le nom contient 'étape_coord', sous la forme 'lon;lat'
    Les arêtes interdites sont dans des champs dont le nom contient 'interdite_coord', sous la même forme.
    """
    # form = forms.RelanceRapide(requête.GET)
    # if not form.is_valid():
    #     print(form.errors)
    # données = dict_of_get(requête.GET)
    # données.update(form.cleaned_data)

    données = récup_données(requête.GET, forms.RelanceRapide)
    
    z_d = g.charge_zone(données["zone"].nom)
    
    départ = Étape.of_dico(requête.GET, "départ", g, z_d)
    arrivée = Étape.of_dico(requête.GET, "arrivée", g, z_d)

    é_inter = []
    é_interdites = []
    
    for c, v in requête.GET.items():
        if "étape_coord" in c:
            num = int(re.match("étape_coord([0-9]*)", c).groups()[0])
            print(num)
            coords = tuple(map(float, v.split(";")))
            a, _ = g.arête_la_plus_proche(coords, z_d)
            é_inter.append((num, ÉtapeArête.of_arête(a, coords)))
            
        elif "interdite_coord" in c:
            coords = tuple(map(float, v.split(";")))
            a, _ = g.arête_la_plus_proche(coords, z_d)
            é_interdites.append(ÉtapeArête.of_arête(a, coords))
            
    é_inter.sort()
    étapes = [départ] + [é for _, é in é_inter] + [arrivée]
    return calcul_itinéraires(requête, requête.GET["pourcentage_détour"], z_d,
                              étapes, étapes_interdites=é_interdites,
                              données=données,
                              bavard=3)




def chaîne_avec_points_virgule_renversée(c: str):
    """
    c contient des point-virgules
    Sortie : la même en inversant l’ordre des morceaux séparés par les points-virgules.
    """
    return ";".join(
        reversed(
            c.split(";")
        )
    )

def trajet_retour(requête):
    """
    Renvoie le résultat pour le trajet retour de celui reçu dans la requête.
    """

    données = récup_données(requête.GET, forms.ToutCaché)
    z_d, étapes, étapes_interdites, ps_détour = z_é_i_d(g, données)
    
    #  Échange départ-arrivée dans le dico de données
    données["départ"], données["arrivée"] = données["arrivée"], données["départ"]
    données["coords_départ"], données["coords_arrivée"] = données["coords_arrivée"], données["coords_départ"]

    #  Étapes à l’envers
    étapes.reverse()
    données["marqueurs_é"] = chaîne_avec_points_virgule_renversée(données["marqueurs_é"])

    return calcul_itinéraires(requête, ps_détour, z_d,
                              étapes,
                              étapes_interdites=étapes_interdites,
                              données=données
                              )




### Fonction principale


def calcul_itinéraires(requête, ps_détour, z_d, étapes, étapes_interdites=[], données={}, bavard=0):
    """
    Entrées : ps_détour (float list ou str)
              z_d (models.Zone)
              noms_étapes (str list)
              rues_interdites (str list), noms des rues interdites.
              étapes (chemin.Étape list or None), si présent sera utilisé au lieu de noms_étapes. Doit contenir aussi départ et arrivée. Et dans ce cas, interdites sera utilisé au lieu de rues_interdites.
              interdites (chemin.Étape list or None), ne passer par aucune arête inclue dans une de ces étapes.
              données : données du formulaire précédent : sera utilisé pour préremplir les formulaires de relance de recherche et d’enregistrement.
    """
    
    if isinstance(ps_détour, str):
        ps_détour = list(map( lambda x: float(x)/100, requête.GET["pourcentage_détour"].split(";")) )
        
    try:
        stats, chemin, noms_étapes, rues_interdites, carte = itinéraire_of_étapes(
            étapes, ps_détour, g, z_d, requête.session,
            rajouter_iti_direct=len(étapes)>2,
            étapes_interdites=étapes_interdites,
            bavard=1,
            où_enregistrer="dijk/templates/dijk/iti_folium.html"
        )
        
        ## Création du gabarit

        suffixe = "".join(noms_étapes) + "texte_étapes" + "".join(rues_interdites)

        vieux_fichier = glob("dijk/templates/dijk/résultat_itinéraire_complet**")
        for f in vieux_fichier:
            os.remove(f)
        head, body, script = récup_head_body_script("dijk/templates/dijk/iti_folium.html")

        nom_fichier_html = f"dijk/résultat_itinéraire_complet{suffixe}"
        if len(nom_fichier_html) > 230:
            nom_fichier_html = nom_fichier_html[:230]
        nom_fichier_html += ".html"

        with open(os.path.join("dijk/templates", nom_fichier_html), "w") as sortie:
            sortie.write(f"""
            {{% extends "dijk/résultat_itinéraire_sans_carte.html" %}}
            {{% block head_début %}}
            {head}
            {{% load static %}}
            <script src="{{% static 'dijk/leaflet-providers.js' %}}" type="text/javascript" > </script>
            {{% endblock %}}
            {{% block carte %}} {body} {{% endblock %}}
            {{% block script %}} <script> {script} </script> {{% endblock %}}
            """)

            
        ## Chargement du gabarit

        def texte_marqueurs(l_é):
            """
            Entrée : liste d’étapes
            Sortie (str) : coords des étapes de type ÉtapeArête séparées par des ;. La première et la dernière étape sont supprimées (départ et arrivée).
            """
            return ";".join(map(
                lambda c: f"{c[0]},{c[1]}",
                [é.coords_ini for é in l_é[1:-1] if isinstance(é, ÉtapeArête)]
            ))

        # Ce dico sera envoyé au gabarit sous le nom de 'post_préc'
        
        données.update({"étapes": ";".join(noms_étapes[1:-1]),
                        "rues_interdites": ";".join(rues_interdites),
                        "pourcentage_détour": ";".join(map(lambda p: str(int(p*100)), ps_détour)),
                        "départ": étapes[0].adresse,
                        "arrivée": étapes[-1].adresse,
                        "zone_t": z_d.nom,
                        "marqueurs_i": texte_marqueurs(étapes_interdites),
                        "marqueurs_é": texte_marqueurs(étapes),
                        })
        
        texte_étapes_inter = énumération_texte(noms_étapes[1:-1])
        return render(requête,
                      nom_fichier_html,
                      {**données,
                       **{"stats": stats,
                          "texte_étapes_inter": texte_étapes_inter,
                          "rues_interdites": énumération_texte(rues_interdites),
                          "chemin": chemin.str_joli(),
                          "post_préc": données,
                          "relance_rapide": forms.RelanceRapide(initial=données),
                          "enregistrer_contrib": forms.ToutCaché(initial=données),
                          "trajet_retour": forms.ToutCaché(initial=données),
                          "fouine": requête.session.get("fouine", None),
                          "la_carte": carte.get_name()
                          }
                       }
                      )

    # Renvoi sur la page d’erreur
    except (PasTrouvé, recup_donnees.LieuPasTrouvé) as e:
        return vueLieuPasTrouvé(requête, e)
    except Exception as e:
        traceback.print_exc()
        return autreErreur(requête, e)







### Ajout d’un nouvel itinéraire ###


def confirme_nv_chemin(requête):
    """
    Traitement du formulaire d’enregistrement d’un nouveau chemin.
    """
    try:

        données = récup_données(requête.POST, forms.ToutCaché)
        z_d, étapes, étapes_interdites, _ = z_é_i_d(g, données)

        nb_lectures = 50

        #noms_étapes = [é for é in requête.POST["étapes"].strip().split(";") if len(é)>0]
        AR = bool_of_checkbox(requête.POST, "AR")
        #rues_interdites = [r for r in requête.POST["rues_interdites"].strip().split(";") if len(r)>0]

        chemins = []
        for id_chemin in requête.POST.keys():
            if id_chemin[:2] == "ps" and requête.POST[id_chemin] == "on":
                pourcentage_détour = int(id_chemin[2:])
                c = Chemin.of_étapes(z_d, étapes, pourcentage_détour, AR, g, étapes_interdites=étapes_interdites, nv_cache=2, bavard=2)
                chemins.append(c)
                for é in c.étapes:
                    print(é.nœuds)
                c_d = c.vers_django(bavard=1)
                
                prop_modif = n_lectures(nb_lectures, g, [c], bavard=1)
                c_d.dernier_p_modif = prop_modif
                c_d.save()

        return render(requête, "dijk/merci.html", {"chemin": chemins, "zone_t": z_d.nom})
    
    except Exception as e:
        traceback.print_exc()
        return autreErreur(requête, e)


### traces gpx ###

def téléchargement(requête):
    """
    Fournit le .gpx, consément dans requête.POST["gpx"]
    """
    try:
        return HttpResponse(
            requête.POST["gpx"].replace("%20", " ").replace("ν", "\n"),
            headers={
                'Content-Type': "application/gpx+xml",
                'Content-Disposition': 'attachment; filename="trajet.gpx"'
            }
        )
    except Exception as e:
        return autreErreur(requête, e)


### Carte cycla ###


def choix_cycla(requête):
    if requête.method == "GET" and requête.GET:
        # On est arrivé ici après remplissage du formulaire
        form = forms.FormCycla(requête.GET)
        if form.is_valid():
            return carte_cycla(requête)
    else:
        # Formulaire pas encore rempli (premier appel)
        form = forms.FormCycla()
    return render(requête, "dijk/cycla_choix.html", {"form": form})


def carte_cycla(requête):
    """
    Renvoie la carte de la cyclabilité de la zone indiquée.
    """
    z_d = Zone.objects.get(id=requête.GET["zone"])
    nom = f"dijk/cycla{z_d}.html"
    print(nom)
    if not os.path.exists("dijk/templates/"+nom) or "force_calcul" in requête.GET:
        if z_d.nom not in g.zones: g.charge_zone(z_d.nom)
    
        dessine_cycla(g, z_d, où_enregistrer="dijk/templates/"+nom, bavard=1)
    return render(requête, nom)



### Gestion des chemins (admin) ###

def affiche_chemins(requête):
    cs = Chemin_d.objects.all()
    n_cs = len(cs)
    print(f"Nombre de chemins : {len(cs)}")
    return render(requête, "dijk/affiche_chemins.html", {"chemins": cs, "nb_chemins": n_cs})


def action_chemin(requête):
    
    if requête.POST["action"] == "voir":
        c = Chemin_d.objects.get(id=requête.POST["id_chemin"])
        g.charge_zone(c.zone.nom)
        étapes = c.étapes()
        d = étapes[0]
        a = étapes[-1]
        return calcul_itinéraires(
            requête, d, a,
            [c.p_détour],
            c.zone,
            étapes[1:-1],
            c.rues_interdites()
        )

    elif requête.POST["action"] == "effacer":
        c = Chemin_d.objects.get(id=requête.POST["id_chemin"])
        c.delete()
        return affiche_chemins(requête)


### Erreurs ###

def vueLieuPasTrouvé(requête, e):
    return render(requête, "dijk/LieuPasTrouvé.html", {"msg": f"{e}"})


def autreErreur(requête, e):
    return render(requête, "dijk/autreErreur.html", {"msg": f"{e.__class__.__name__} : {e}"})


### Stats ###

def recherche_pourcentages(requête):
    return render(requête, "dijk/recherche_pourcentages.html")

def vue_pourcentages_piétons_pistes_cyclables(requête, ville=None):
    """
    Renvoie un tableau avec les pourcentages de voies piétonnes et de pistes cyclables pour les villes dans requête.POSTE["villes"]. Lequel est un str contenant les villes séparées par des virgules.
    """
    from dijk.progs_python.stats import pourcentage_piéton_et_pistes_cyclables
    if ville:
        villes=[ville]
    else:
        villes = requête.POST["villes"].split(";")
    res = []
    for v in villes:
        res.append( (v,) + pourcentage_piéton_et_pistes_cyclables(v))
    return render(requête, "dijk/pourcentages.html", {"stats":res})



### Auto complétion ###


def pour_complétion(requête, nbMax=15):
    """
    Renvoie la réponse nécessitée par autocomplete.
    Laisse tel quel la partie avant le dernier ;
    Découpe l’adresse en (num? bis_ter? rue(, ville)?), et cherche des complétions pour rue et ville.
    nbMax : nb max de résultat. S’il y en a plus, aucun n’est renvoyé.
    """
    mimeType = "application/json"
    if "term" in requête.GET:

        # id de la zone
        if "zone_id" not in requête.session:
            z_d = Zone.objects.get(nom=requête.session["zone"])
            requête.session["zone_id"] = z_d.pk
            z_id = z_d.pk
        else:
            z_id = requête.session["zone_id"]
            z_d = Zone.objects.get(pk=z_id)
        

        # Découpage de la chaîne à chercher
        tout = requête.GET["term"].split(";")
        à_chercher = prétraitement_rue(tout[-1])
        num, bis_ter, rue, ville = découpe_adresse(à_chercher)
        print(f"Recherche de {rue}")
        début = " ".join(x for x in [num, bis_ter] if x)
        if début: début += " "
        
        def chaîne_à_renvoyer(adresse, ville=None, parenthèse=None):
            res = ";".join(tout[:-1] + [début+adresse])
            if parenthèse:
                res += f" ({parenthèse})"
            if ville: res += ", " + ville
            return res

        # Villes de la zone z_id
        villes = Ville_Zone.objects.filter(zone=z_id, ville__nom_norm__icontains=ville)
        req_villes = Subquery(villes.values("ville"))

        dicos = []

        # Complétion dans l’arbre lexicographique (pour les fautes de frappe...)
        # Fonctionne sauf qu’on ne récupère pas la ville pour l’instant
        # dans_l_arbre = g.arbre_lex_zone[z_d].complétion(à_chercher, tol=2, n_max_rés=nbMax)
        # print(dans_l_arbre)
        
        
        ## Recherche dans les rues de la base
        dans_la_base = Rue.objects.filter(nom_norm__icontains=rue, ville__in=req_villes).prefetch_related("ville")
        for rue_trouvée in dans_la_base:
            dicos.append({"label": chaîne_à_renvoyer(rue_trouvée.nom_complet, rue_trouvée.ville.nom_complet)})

        if len(dicos) > nbMax:
            print(f"Nombre de résultats : {len(dicos)}. C’est trop.")
            return HttpResponse("fail", mimeType)

        
        ## Recherche dans les amenities
        amenities = Amenity.objects.filter(nom__icontains=rue, ville__in=req_villes).prefetch_related("ville", "type_amenity")
        chaînes_déjà_présentes = set()
        print(f"{len(amenities)} amenities trouvées")
        for a in amenities:
            #chaîne = chaîne_à_renvoyer(a.nom, a.ville.nom_complet, parenthèse=a.type_amenity.nom_français)
            chaîne = str(a)
            if chaîne not in chaînes_déjà_présentes:
                chaînes_déjà_présentes.add(chaîne)
                dicos.append({"label": chaîne, "lon": a.lon, "lat": a.lat})
        if len(dicos) > nbMax:
            print(f"Nombre de résultats : {len(dicos)}. C’est trop.")
            return HttpResponse("fail", mimeType)

        
        ## Recherche dans les caches
        for truc in Cache_Adresse.objects.filter(adresse__icontains=rue, ville__in=req_villes).prefetch_related("ville"):
            print(f"Trouvé dans Cache_Adresse : {truc}")
            dicos.append({"label": chaîne_à_renvoyer(truc.adresse, truc.ville.nom_complet)})
            
        for chose in CacheNomRue.objects.filter(Q(nom__icontains=rue) | Q(nom_osm__icontains=rue), ville__in=req_villes).prefetch_related("ville"):
            print(f"Trouvé dans CacheNomRue : {chose}")
            dicos.append({"label": chaîne_à_renvoyer(chose.nom_osm, chose.ville.nom_complet)})
            
            
        # Création du json à renvoyer
        rés = json.dumps(dicos)
        
    else:
        rés="fail"
        

    return HttpResponse(rés, mimeType)
