# -*- coding:utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse


from dijk.progs_python import params
from dijk.progs_python.lecture_adresse.normalisation import VILLE_DÉFAUT
from dijk.progs_python.utils import itinéraire, dessine_chemin, dessine_cycla
from dijk.progs_python.init_graphe import charge_graphe
from dijk.progs_python.chemins import Chemin, chemins_of_csv
from dijk.progs_python.lecture_adresse.recup_noeuds import PasTrouvé
from dijk.progs_python.recup_donnees import LieuPasTrouvé
from dijk.progs_python.apprentissage import n_lectures, lecture_jusqu_à_perfection

from datetime import datetime
from glob import glob
import os


g=charge_graphe()

# Create your views here.

def index(requête):
    return render(requête, "dijk/index.html", {"ville":VILLE_DÉFAUT})

def limitations(requête):
    return render(requête, "dijk/limitations.html", {})

def bool_of_checkbox(dico, clef):
    """Transforme la valeur venue d’une checkbox via un POST en un brave booléen."""
    try:
        if dico[clef]=="on":
            return True
        else:
            return False
    except KeyError:
        return False

def énumération_texte(l):
    """
    Entrée : liste de str
    Sortie : une str contenant les éléments de l séparés par des virgules, sauf dernier qui est séparé par le mot « et »
    """
    if len(l)==0:
        return ""
    elif len(l)==1:
        return l[0]
    else:
        return ", ".join(l[:-1]) + " et " + l[-1]

    
### Recherche d’itinéraire simple ###

def récup_head_body_script(chemin):
    """ Entrée : adresse d’un fichier html
        Sortie : la partie body de celui-ci
    """
    with open(chemin) as entrée:
        tout=entrée.read()
        
        head, suite = tout.split("</head>")
        head = head.split("<head>")[1]
        
        body, suite = suite.split("</body>")
        body = body.split("<body>")[1]

        script = suite.split("<script>")[1].split("</script>")[0]
    return head, body, script


def visualisation_nv_chemin(requête):
    return render(requête, "dijk/iti_folium.html", {})

    
def vue_itinéraire(requête):
    """ Doit récupérer le résultat du formulaire via un post."""

    # Récupération des données du post
    d=requête.POST["départ"]
    a=requête.POST["arrivée"]
    noms_étapes = [é for é in requête.POST["étapes"].strip().split(";") if len(é)>0]
    texte_étapes = énumération_texte(noms_étapes)
    ps_détour = list(map( lambda x: int(x)/100, requête.POST["pourcentage_détour"].split(";")) )
    p_détour_moyen = int(sum(ps_détour)/len(ps_détour)*100)
    rues_interdites = [r for r in requête.POST["rues_interdites"].strip().split(";") if len(r)>0]
    print(f"Recherche d’itinéraire entre {d} et {a} avec étapes {noms_étapes} et rues interdites = {rues_interdites}.")

    # Calcul des itinéraires
    try:
        stats = itinéraire(
            d, a, ps_détour, g, rajouter_iti_direct=len(noms_étapes)>0,
            noms_étapes=noms_étapes,
            rues_interdites=rues_interdites,
            bavard=4, où_enregistrer="dijk/templates/dijk/iti_folium.html"
        )
    except (PasTrouvé, LieuPasTrouvé) as e:
        return vueLieuPasTrouvé(requête, e)
    
    # Création du template
    suffixe = d+texte_étapes+a+"".join(rues_interdites)
    vieux_fichier = glob("dijk/templates/dijk/résultat_itinéraire_complet**")
    for f in vieux_fichier:
        os.remove(f)
    head, body, script = récup_head_body_script("dijk/templates/dijk/iti_folium.html")
    with open(f"dijk/templates/dijk/résultat_itinéraire_complet{suffixe}.html", "w") as sortie:
        sortie.write(f"""
        {{% extends "dijk/résultat_itinéraire_sans_carte.html" %}}
        {{% block head_début %}}  {head}  {{% endblock %}}
        {{% block carte %}} {body} {{% endblock %}}
        {{% block script %}} <script> {script} </script> {{% endblock %}}
        """)

    # Chargement du template
    return render(requête, f"dijk/résultat_itinéraire_complet{suffixe}.html",
                  {"stats": stats,
                   "départ":d, "arrivée":a,
                   "étapes": texte_étapes,
                   "rues_interdites": énumération_texte(rues_interdites),
                   "post_préc":requête.POST, "p_détour_moyen":p_détour_moyen
                   }
                  )




### Ajout d’un nouvel itinéraire ###

def contribution(requête):
    """ Page du formulaire pour ajouter un chemin.
    À remplacer par une page « Comment aider » ?
    """
    return render(requête, "dijk/contribution.html", {})


        
def confirme_nv_chemin(requête):
    nb_lectures=10
    #(étapes, p_détour, AR) = requête.session["chemin_à_valider"]
    d=requête.POST["départ"]
    a=requête.POST["arrivée"]
    noms_étapes = [é for é in requête.POST["étapes"].strip().split(";") if len(é)>0]
    pourcentage_détour = int(requête.POST["pourcentage_détour"])
    AR = bool_of_checkbox(requête.POST, "AR")
    rues_interdites = [r for r in requête.POST["rues_interdites"].strip().split(";") if len(r)>0]
    print(f"étapes : {noms_étapes}, pourcentage détour : {pourcentage_détour}, AR : {AR}, rues interdites : {rues_interdites}\n")
    
    c = Chemin.of_étapes([d]+noms_étapes+[a], pourcentage_détour, AR, g, noms_rues_interdites=rues_interdites, bavard=2)
    c.sauv(bavard=1)
    n_lectures(nb_lectures, g, [c], bavard=1)
    
    #tousLesChemins = chemins_of_csv(g, bavard=1)
    #n_lectures(nb_lectures, g, tousLesChemins, bavard=1) # Trop long... À mettre ailleurs ? Dans un cron ?
    g.sauv_cache()
    g.sauv_cycla()
    return render(requête, "dijk/merci.html", {"chemin":c})



### Carte cycla ###

def carte_cycla(requête):
    dessine_cycla(g, où_enregistrer="dijk/templates/dijk")
    return render(requête, "dijk/cycla.html")


### Erreurs ###

def vueLieuPasTrouvé(requête, e):
    return render(requête, "dijk/LieuPasTrouvé.html", {"msg":str(e)})
