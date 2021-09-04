from django.shortcuts import render
from django.http import HttpResponse
from dijk.progs_python.utils import itinéraire, dessine_chemin
from dijk.progs_python.init_graphe import charge_graphe
from dijk.progs_python.chemins import Chemin
g=charge_graphe()

# Create your views here.

def index(requête):
    return render(requête, "dijk/index.html", {})


### Recherche d’itinéraire simple ###

def vue_itinéraire_direct(requête, départ, arrivée, pourcentage_détour):
    """ Plus pour test a priori"""
    print(f"Recherche d’itinéraire entre {départ} et {arrivée}.")
    res = itinéraire(départ, arrivée, pourcentage_détour/100, g, bavard=4, où_enregistrer="dijk/templates/dijk" )
    print(f"fichier enregistré dans {res}")
    return render(requête, "dijk/résultat_itinéraire.html", {})


def vue_itinéraire(requête):
    """ Celle-ci doit récupérer le résultat du formulaire via un post."""
    d=requête.POST["départ"]
    a=requête.POST["arrivée"]
    p_détour= int(requête.POST["pourcentage_détour"])/100
    print(f"Recherche d’itinéraire entre {d} et {a}.")
    itinéraire(d, a, p_détour, g, bavard=4, où_enregistrer="dijk/templates/dijk" )
    return render(requête, "dijk/résultat_itinéraire.html", {})



### Ajout d’un nouvel itinéraire ###

def contribution(requête):
    """ Page du formulaire pour ajouter un chemin."""
    return render(requête, "dijk/contribution.html", {})

def visualisation_nv_chemin(requête):
    return render(requête, "dijk/nouveau_chemin.html", {})

def vérif_nv_chemin(requête):
    d=requête.POST["départ"]
    a=requête.POST["arrivée"]
    p_détour= int(requête.POST["pourcentage_détour"])/100
    étapes = requête.POST["étapes"].split(";")
    AR=requête.POST["AR"]
    print(AR)

    c = Chemin.of_étapes([d]+étapes+[a], p_détour,  AR, g, bavard=2)
    dessine_chemin(c, g, où_enregistrer="dijk/templates/dijk", bavard=2)
    return render(requête, "dijk/vérif_nouveau_chemin.html", {"chemin":c})

        
