from django.shortcuts import render
from django.http import HttpResponse
from dijk.progs_python.utils import itinéraire, dessine_chemin, dessine_cycla
from dijk.progs_python.init_graphe import charge_graphe
from dijk.progs_python.chemins import Chemin, chemins_of_csv
from dijk.progs_python.apprentissage import n_lectures
g=charge_graphe()

# Create your views here.

def index(requête):
    return render(requête, "dijk/index.html", {})

def bool_of_checkbox(dico, clef):
    """Transforme la valeur venue d’une checkbox via un POST en un brave booléen."""
    try:
        if dico[clef]=="on":
            return True
        else:
            return False
    except KeyError:
        return False
    

### Recherche d’itinéraire simple ###


def vue_itinéraire(requête):
    """ Celle-ci doit récupérer le résultat du formulaire via un post."""
    d=requête.POST["départ"]
    a=requête.POST["arrivée"]
    ps_détour = list(map( lambda x: int(x)/100, requête.POST["pourcentage_détour"].split(";")) )
    print(f"Recherche d’itinéraire entre {d} et {a}.")
    longueur=itinéraire(d, a, ps_détour, g, bavard=4, où_enregistrer="dijk/templates/dijk/résultat_itinéraire.html" )
    return render(requête, "dijk/résultat_itinéraire.html", {})



### Ajout d’un nouvel itinéraire ###

def contribution(requête):
    """ Page du formulaire pour ajouter un chemin."""
    return render(requête, "dijk/contribution.html", {})


def visualisation_nv_chemin(requête):
    return render(requête, "dijk/nouveau_chemin.html", {})


def vérif_nv_chemin(requête, debug=0):
    d=requête.POST["départ"]
    a=requête.POST["arrivée"]
    pourcent_détour= int(requête.POST["pourcentage_détour"])
    étapes = requête.POST["étapes"].split(";")
    AR = bool_of_checkbox(requête.POST, "AR")
    if debug>0: print(AR)

    c = Chemin.of_étapes([d]+étapes+[a], pourcent_détour,  AR, g, bavard=2)
    longueur,longueur_direct = dessine_chemin(c, g, où_enregistrer="dijk/templates/dijk/nouveau_chemin.html", bavard=2)
    requête.session["chemin_à_valider"] = ([d]+étapes+[a], pourcent_détour, AR) # session est un dictionnaire pour stocker du bazar propre à un utilisateur.
    return render(requête, "dijk/vérif_nouveau_chemin.html", {"chemin":c, "longueurs":(longueur, longueur_direct)})

        
def confirme_nv_chemin(requête):
    nb_lectures=10
    (étapes, p_détour, AR) = requête.session["chemin_à_valider"]
    print(étapes, p_détour, AR, "\n")
    c = Chemin.of_étapes(étapes, p_détour, AR, g)
    c.sauv()
    n_lectures(nb_lectures, g, [c], bavard=1)
    tousLesChemins = chemins_of_csv(g, bavard=1)
    #n_lectures(nb_lectures, g, tousLesChemins, bavard=1) # Trop long... À mettre ailleurs ? Dans un cron ?
    g.sauv_cache()
    g.sauv_cycla()
    return render(requête, "dijk/merci.html", {"chemins":tousLesChemins})



### Carte cycla ###

def carte_cycla(requête):
    dessine_cycla(g, où_enregistrer="dijk/templates/dijk")
    return render(requête, "dijk/cycla.html")
