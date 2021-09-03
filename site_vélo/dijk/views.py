from django.shortcuts import render
from django.http import HttpResponse
from dijk.progs_python.utils import itinéraire
from dijk.progs_python.init_graphe import charge_graphe
g=charge_graphe()

# Create your views here.

def index(requête):
    return render(requête, "dijk/index.html", {})


def vue_itinéraire_direct(requête, départ, arrivée, pourcentage_détour):
    print(f"Recherche d’itinéraire entre {départ} et {arrivée}.")
    res = itinéraire(départ, arrivée, pourcentage_détour/100, g, bavard=4, où_enregistrer="dijk/templates/dijk" )
    print(f"fichier enregistré dans {res}")
    return render(requête, "dijk/résultat_itinéraire.html", {})


def vue_itinéraire(requête):
    """ Celle-ci doit récupérer le résultat du formulaire via un post."""
    pass
