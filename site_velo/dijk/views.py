# -*- coding:utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import  Subquery, Q
import time
from datetime import datetime
from glob import glob
import os
import forms
import traceback
import json
import re


tic0=time.perf_counter()

from dijk.progs_python.params import LOG
from petites_fonctions import chrono, union_liste
from dijk.progs_python.lecture_adresse.normalisation import Adresse
tic=chrono(tic0, "params, petites_fonctions, normalisation", bavard=3)

from dijk.progs_python.chemins import Chemin, chemins_of_csv, Étape, ÉtapeArête
tic=chrono(tic, "chemins", bavard=3)

#from dijk.progs_python.init_graphe import charge_graphe
#tic=chrono(tic, "charge_graphe", bavard=3)

from dijk.progs_python.lecture_adresse.recup_noeuds import PasTrouvé
from dijk.progs_python.lecture_adresse.normalisation0 import prétraitement_rue
from dijk.progs_python import recup_donnees
from dijk.progs_python.apprentissage import n_lectures, lecture_jusqu_à_perfection, lecture_plusieurs_chemins
from dijk.progs_python.bib_vues import bool_of_checkbox, énumération_texte, sans_style, récup_head_body_script
tic=chrono(tic, "recup_noeuds, recup_donnees, bib_vues", bavard=3)

from dijk.progs_python.utils import itinéraire, dessine_chemin, dessine_cycla, itinéraire_of_étapes
chrono(tic, "utils", bavard=3)

from graphe_par_django import Graphe_django
from dijk.progs_python.lecture_adresse.normalisation0 import découpe_adresse

g=Graphe_django()


from dijk.models import Chemin_d, Zone, Rue, Ville_Zone, Cache_Adresse, CacheNomRue




chrono(tic0, "Chargement total\n\n", bavard=3)

# Create your views here.


#https://stackoverflow.com/questions/18176602/how-to-get-the-name-of-an-exception-that-was-caught-in-python
def get_full_class_name(obj):
    module = obj.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return obj.__class__.__name__
    return module + '.' + obj.__class__.__name__



def recherche(requête, zone_t):
    z_d = g.charge_zone(zone_t)
    requête.session["zone"]=zone_t
    requête.session["zone_id"] = z_d.pk
    return render(requête, "dijk/recherche.html", {"ville":z_d.ville_défaut, "zone_t":zone_t})


def fouine(requête):
    requête.session["fouine"] = True
    return choix_zone(requête) 

def limitations(requête):
    return render(requête, "dijk/limitations.html", {})

def index(requête):
    return render(requête, "dijk/index.html", {"zones":Zone.objects.all()})

def mode_demploi(requête):
    return render(requête, "dijk/mode_demploi.html", {})

def contribution(requête):
    return render(requête, "dijk/contribution.html", {})


### Recherche d’itinéraire simple ###


def visualisation_nv_chemin(requête):
    return render(requête, "dijk/iti_folium.html", {})

    
def vue_itinéraire(requête):
        """ Doit récupérer le résultat du formulaire via un get."""

    #try :
        # Récupération des données du post
        d=requête.GET["départ"]
        a=requête.GET["arrivée"]
        z_d = g.charge_zone(requête.GET["zone_t"]) # On pourrait arriver ici sans être passé par la page recherche (?)
        #z_d = Zone.objects.get(nom=requête.GET["zone_t"])

        noms_étapes = [é for é in requête.GET["étapes"].strip().split(";") if len(é)>0]

        ps_détour = list(map( lambda x: float(x)/100, requête.GET["pourcentage_détour"].split(";")) )

        rues_interdites = [r for r in requête.GET["rues_interdites"].strip().split(";") if len(r)>0]
        print(f"Recherche d’itinéraire entre {d} et {a} avec étapes {noms_étapes} et rues interdites = {rues_interdites}.")

        return calcul_itinéraires(requête, d, a, ps_détour, z_d, noms_étapes, rues_interdites)
    
    #except Exception as e:
    #    return autreErreur(requête, e)


def calcul_itinéraires(requête, d, a, ps_détour, z_d, noms_étapes, rues_interdites, étapes=None, interdites={}, bavard=0):
    """
    Entrées : ps_détour (float list ou str)
              z_d (models.Zone)
              noms_étapes (str list)
              rues_interdites (str list), noms des rues interdites.
              étapes (chemin.Étape list or None), si présent sera utilisé au lieu de noms_étapes. Doit contenir aussi départ et arrivée. Et dans ce cas, interdites sera utilisé au lieu de nues_interdites.
    """
    
    if isinstance(ps_détour, str):
        ps_détour = list(map( lambda x: float(x)/100, requête.GET["pourcentage_détour"].split(";")) )
        
    try:
        if étapes:
            # On saute le calcul des étapes
            stats, chemin, d, a, noms_étapes, carte = itinéraire_of_étapes(
            étapes, ps_détour, g, z_d, requête.session,
            rajouter_iti_direct=len(étapes)>2,
            interdites=interdites,
            bavard=10,
            où_enregistrer="dijk/templates/dijk/iti_folium.html"
        )
            rues_interdites=[]
        else:
            stats, chemin, d, a, noms_étapes, rues_interdites, carte = itinéraire(
                d, a, ps_détour, g, z_d, requête.session,
                rajouter_iti_direct=len(noms_étapes)>0,
                noms_étapes=noms_étapes,
                rues_interdites=rues_interdites,
                bavard=10,
                où_enregistrer="dijk/templates/dijk/iti_folium.html"
            )
    
        # Création du template
        texte_étapes = énumération_texte(noms_étapes)
        suffixe = d+texte_étapes+a+"".join(rues_interdites)

        vieux_fichier = glob("dijk/templates/dijk/résultat_itinéraire_complet**")
        for f in vieux_fichier:
            os.remove(f)
        head, body, script = récup_head_body_script("dijk/templates/dijk/iti_folium.html")

        nom_fichier_html = f"dijk/résultat_itinéraire_complet{suffixe}"
        if len(nom_fichier_html)>230: nom_fichier_html=nom_fichier_html[:230]
        nom_fichier_html+=".html"

        with open(os.path.join("dijk/templates", nom_fichier_html), "w") as sortie:
            sortie.write(f"""
            {{% extends "dijk/résultat_itinéraire_sans_carte.html" %}}
            {{% block head_début %}}  {head}  {{% endblock %}}
            {{% block carte %}} {body} {{% endblock %}}
            {{% block script %}} <script> {script} </script> {{% endblock %}}
            """)


        # Chargement du template
        #p_détour_moyen = int(sum(ps_détour)/len(ps_détour)*100)
        # Ce dico sera envoyé au gabarit sous le nom de 'post_préc'
        données = {"étapes": ";".join(noms_étapes), "rues_interdites": ";".join(rues_interdites),
                   "pourcentage_détour": ";".join(map(lambda p : str(int(p*100)), ps_détour)),
                   "départ":d,
                   "arrivée":a,
                   "zone_t":z_d.nom,
                   }
        #toutes_les_rues = Rue.objects.filter(ville__zone = z_d)
        return render(requête,
                      nom_fichier_html,
                      {**données,
                       **{"stats": stats,
                           "étapes": texte_étapes,
                           "rues_interdites": énumération_texte(rues_interdites),
                           "chemin":chemin.str_joli(),
                           "post_préc":données,
                           "relance_rapide":forms.RelanceRapide(initial=données),
                           "fouine": requête.session.get("fouine", None),
                           "la_carte": carte.get_name()
                       }}
                      )

    # Renvoi sur la page d’erreur
    except (PasTrouvé, recup_donnees.LieuPasTrouvé) as e: # Ceci ne fonctionne pas...
        return vueLieuPasTrouvé(requête, e)
    except Exception as e:
        traceback.print_exc()
        return autreErreur(requête, e)

    
def relance_rapide(requête):
    """
    Relance un calcul à partir du résultat du formulaire de relance rapide.
    Les étapes sont dans des champs dont le nom contient 'étape_coord', sous la forme 'lon;lat'
    """
    print(requête.GET)
    z_d = g.charge_zone(requête.GET["zone_t"])
    départ = Étape.of_texte(requête.GET["départ"], g, z_d)
    arrivée = Étape.of_texte(requête.GET["arrivée"],g, z_d)


    inter = []
    for c, v in requête.GET.items():
        if "étape_coord" in c:
            print(v)
            coords = tuple(map(float, v.split(";")))
            a, _ = g.arête_la_plus_proche(coords, z_d)
            inter.append((c[11:], ÉtapeArête.of_arête(a, coords)))
    inter.sort()
    étapes = [départ] + [é for _, é in inter] + [arrivée]
    return calcul_itinéraires(requête, départ, arrivée, requête.GET["pourcentage_détour"], z_d, [], [], étapes = étapes, bavard=10)
    
    
    
def trajet_retour(requête):
    """
    Renvoie le résultat pour le trajet retour de celui reçu dans la requête.
    """
    départ=requête.GET["arrivée"]
    arrivée=requête.GET["départ"]
    rues_interdites = [r for r in requête.GET["rues_interdites"].strip().split(";") if len(r)>0]
    
    noms_étapes = [é for é in requête.GET["étapes"].strip().split(";") if len(é)>0]
    z_d = g.charge_zone(requête.GET["zone_t"])
    ps_détour = list(map( lambda x: float(x)/100, requête.GET["pourcentage_détour"].split(";")) )

    return calcul_itinéraires(requête, départ, arrivée, ps_détour, z_d, noms_étapes, rues_interdites)




### Ajout d’un nouvel itinéraire ###


def confirme_nv_chemin(requête):
    """
    Traitement du formulaire d’enregistrement d’un nouveau chemin.
    """
    try:
        nb_lectures=50
        #(étapes, p_détour, AR) = requête.session["chemin_à_valider"]
        d=requête.POST["départ"]
        a=requête.POST["arrivée"]
        noms_étapes = [é for é in requête.POST["étapes"].strip().split(";") if len(é)>0]
        #pourcentage_détour = int(requête.POST["pourcentage_détour"])
        AR = bool_of_checkbox(requête.POST, "AR")
        rues_interdites = [r for r in requête.POST["rues_interdites"].strip().split(";") if len(r)>0]
        zone=Zone.objects.get(nom=requête.POST["zone_t"])
        print(f"étapes : {noms_étapes}, AR : {AR}, rues interdites : {rues_interdites}\n")


        chemins=[]
        for id_chemin in requête.POST.keys():
            if id_chemin[:2]=="ps" and requête.POST[id_chemin]=="on":
                pourcentage_détour = int(id_chemin[2:])
                print(f"pourcentage_détour : {pourcentage_détour}")
                # nv_cache = 2 ici.
                c = Chemin.of_étapes(zone, [d]+noms_étapes+[a], pourcentage_détour, AR, g, noms_rues_interdites=rues_interdites, nv_cache=2, bavard=2)
                chemins.append(c)
                c_d=c.vers_django(bavard=1)
                prop_modif = n_lectures(nb_lectures, g, [c], bavard=1)
                print(prop_modif)
                c_d.dernier_p_modif=prop_modif
                c_d.save()

        return render(requête, "dijk/merci.html", {"chemin":chemins, "zone_t":zone.nom})
    except Exception as e:
        traceback.print_exc()
        return autreErreur(requête, e)
    

### traces gpx ###

def téléchargement(requête):
    """
    Fournit le .gpx, consément dans requête.POST["gpx"]
    """
    try :
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

# def cycla_choix(requête):
#     """
#     Renvoie la page de choix de la zone pour laquelle afficher la cycla.
#     """
#     zones = Zone.objects.all()
#     return render(requête, "dijk/cycla_choix.html", {"zones":zones})



# Version formulaire de Django
def choix_cycla(requête):
    if requête.method == "POST":
        # On est arrivé ici après remplissage du formulaire
        form = forms.FormCycla(requête.POST)
        if form.is_valid():
            return carte_cycla(requête)
    else:
        # Formulaire pas encore rempli (premier appel)
        form = forms.FormCycla()
    return render(requête, "dijk/cycla_choix.html", {"form":form})


def choix_zone(requête):
    if requête.method == "POST":
        form = forms.ChoixZone(requête.POST)
        if form.is_valid():
            z_d = Zone.objects.get(pk=requête.POST["zone"])
            return recherche(requête, z_d.nom)
    else:
        form = forms.ChoixZone()
        print(f"Requête pas POST, formulaire créé : {form}")
    return render(requête, "dijk/index.html", {"form":form})



def carte_cycla(requête):
    """
    Renvoie la carte de la cyclabilité de la zone indiquée.
    """
    z_d = Zone.objects.get(id=requête.POST["zone"])
    nom = f"dijk/cycla{z_d}.html"
    if not os.path.exists("dijk/templates/"+nom) or "force_calcul" in requête.POST:
        if z_d.nom not in g.zones : g.charge_zone(z_d.nom)
    
        dessine_cycla(g, z_d, où_enregistrer="dijk/templates/"+nom, bavard=1)
    return render(requête, nom)



### Gestion des chemins (admin) ###

def affiche_chemins(requête):
    cs = Chemin_d.objects.all()
    n_cs = len(cs)
    print(f"Nombre de chemins : {len(cs)}")
    return render(requête, "dijk/affiche_chemins.html", {"chemins": cs, "nb_chemins":n_cs })


def action_chemin(requête):
    
    if requête.POST["action"]=="voir":
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

    elif requête.POST["action"]=="effacer":
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


def pour_complétion(requête, nbMax = 10):
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
            z_d = Zone.objects.get(nom = requête.session["zone"])
            requête.session["zone_id"] = z_d.pk
        z_id = requête.session["zone_id"]

        # découpage de la chaîne à chercher
        tout = requête.GET["term"].split(";")
        à_chercher = prétraitement_rue(tout[-1])
        num, bis_ter, rue, ville = découpe_adresse(à_chercher)
        print(f"Recherche de {rue}")
        début = " ".join(x for x in [num, bis_ter] if x)
        if début: début+=" "
        
        def chaîne_à_renvoyer(adresse, ville=None):
            res = ";".join(tout[:-1]+[début+adresse])
            if ville: res+= ", "+ville
            return res

        # Villes de la zone z_id
        villes = Ville_Zone.objects.filter(zone=z_id, ville__nom_norm__icontains=ville)
        req_villes = Subquery(villes.values("ville"))

        dicos=[]
        
        # Recherche dans les rues de la base
        dans_la_base = Rue.objects.filter(nom_norm__icontains=rue, ville__in =req_villes ).prefetch_related("ville")
        for rue_trouvée in dans_la_base:
            dicos.append( {"label": chaîne_à_renvoyer(rue_trouvée.nom_complet, rue_trouvée.ville.nom_complet)})

        if len(dicos)>nbMax:
            print(f"Nombre de résultats : {len(dicos)}. C’est trop.")
            return HttpResponse("fail", mimeType)
        
        # Recherche dans les caches
        for truc in Cache_Adresse.objects.filter(adresse__icontains=rue, ville__in =req_villes).prefetch_related("ville"):
            print(f"Trouvé dans Cache_Adresse : {truc}")
            dicos.append( {"label": chaîne_à_renvoyer(truc.adresse, truc.ville.nom_complet)})
            
        for chose in CacheNomRue.objects.filter(Q(nom__icontains=rue) | Q(nom_osm__icontains=rue), ville__in=req_villes).prefetch_related("ville"):
            print(f"Trouvé dans CacheNomRue : {chose}")
            dicos.append( {"label": chaîne_à_renvoyer(chose.nom_osm, chose.ville.nom_complet)})
            
        rés = json.dumps(dicos)
        
    else:
        rés="fail"
        

    return HttpResponse(rés, mimeType)
