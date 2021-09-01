from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.

def index(requête):
    return HttpResponse(f"Voici l'index de l'application dijk. Voici la requête reçue : {requête}")

def itinéraire(requête, départ, arrivée):
    return HttpResponse(f"Recherche d'itinéraire entre {départ} et {arrivée}.")
