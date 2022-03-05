# -*- coding:utf-8 -*-

### Fonctions diverses pour utiliser le logiciel

from time import perf_counter
from petites_fonctions import chrono, deuxConséc
import dijk.models as mo
from params import TMP
#from importlib import reload  # recharger un module après modif
import subprocess
#import networkx as nx  # graphe
from dijk.models import Zone
#from osmnx import plot_graph_folium
from folium.plugins import Fullscreen, LocateControl

tic=perf_counter()
from mon_folium import  folium_of_chemin, ajoute_marqueur, folium_of_arêtes
chrono(tic, "mon_folium", bavard=2)

#ox.config(use_cache=True, log_console=True)
#from module_graphe import graphe  #ma classe de graphe
#import récup_données as rd
#import apprentissage
import dijkstra

tic=perf_counter()
import chemins  # classe chemin et lecture du csv
chrono(tic, "chemins", bavard=2)

from lecture_adresse.normalisation import normalise_rue, normalise_ville
import os


tic=perf_counter()
import folium
chrono(tic, "folium", bavard=2)

from dijk.models import Chemin_d
import apprentissage as ap
from django.db import transaction

import gpxpy

def liste_Arête_of_iti(g, iti, p_détour):
    """
    Entrée : iti (int list), liste d'id osm
    Sortie : liste d'Arêtes
    """
    tic=perf_counter()
    res = [g.meilleure_arête(s,t,p_détour) for (s,t) in deuxConséc(iti)]
    chrono(tic, "conversion de l'itinéraire en liste d'Arêtes.")
    return res


DICO_PROFIl={
    0:("Le plus court",
       "Le trajet le plus court tenant compte des contraintes indiquées."
       ),
    15:("Intermédiaire",
        "Un cycliste de profil « intermédiaire » rallonge en moyenne ses trajets de 10% pour éviter les rues désagréables. Il rallongera son trajet de 15% pour remplacer un itinéraire entièrement non aménagé par un itinéraire entièrement sur piste cyclable."
        ),
    30:("Priorité confort",
        "Un cycliste de profil « priorité confort » rallonge en moyenne ses trajets de 15% pour passer par les zones plus agréables. Il pourra faire un détour de 30% pour remplacer un itinéraire entièrement non aménagé par un itinéraire entièrement sur piste cyclable."
        )
}

def légende_et_aide(p_détour):
    pourcent = int(100*p_détour)
    if pourcent in DICO_PROFIl:
        return DICO_PROFIl[pourcent]
    else:
        return f"Profil détour {pourcent}%", ""


def itinéraire(départ, arrivée, ps_détour, g, z_d, session,
               rajouter_iti_direct=True, noms_étapes=[], rues_interdites=[],
               où_enregistrer=os.path.join(TMP, "itinéraire.html"),
               bavard=0, ouvrir=False):
    """ 
    Entrées :
      - ps_détour (float list), liste des proportion de détour pour lesquels afficher un chemin.
      - g (graphe)
      - z_d (Zone), sert pour récupérer la ville défaut.
      - session (dic), le dico de la session Django
      - départ, arrivée (str) Seront lues par chemins.Étape.
      - noms_étapes (str list), liste de noms d’étapes intermédiaires. Seront également lues par chemin.Étape.

    Effet :  Crée une page html contenant l’itinéraire demandé, et l’enregistre dans où_enregistrer

    Sortie : (liste de dicos (légende, aide, id, p_détour, longueur, longueur ressentie, couleur, gpx) pour les itinéraires obtenus,
              objet Chemin correspondant au dernier p_détour,
             d, a, noms_étapes
             )
             id est la chaîne 'ps'+str(int(100*p_détour)). Servira de champ id aux formulaires.
             aide sera affichée en infobulle dans les pages de résultat.
             départ, arrivée, noms_étapes sont les valeurs après correction d’éventuelles fautes de frappe
    """

    ps_détour.sort() # Pour être sûr que l’éventuel 0 est en premier.
    
    ## Calcul des étapes
    tic0 = perf_counter()

    d = chemins.Étape(départ, g, z_d, bavard=bavard-1)
    if bavard>0: print(f"Départ trouvé : {d}, {d.nœuds}")

    a = chemins.Étape(arrivée, g, z_d, bavard=bavard-1)
    if bavard>0: print(f"Arrivée trouvé : {a}")
    
    étapes = [chemins.Étape(é, g, z_d, bavard=bavard-1) for é in noms_étapes]


    ## Arêtes interdites
    interdites = chemins.arêtes_interdites(g, z_d, rues_interdites, bavard=bavard)
    tic = chrono(tic0, "Calcul des étapes et arêtes interdites.")
    
    np = len(ps_détour)
    à_dessiner = []
    res = []

    def traite_un_chemin(c, coul, légende, aide):
        iti_d, l_ressentie = g.itinéraire(c, bavard=bavard-1)
        à_dessiner.append( (iti_d, coul, p))
        #nom_gpx = hash(c)
        
        res.append({"légende": légende,
                    "aide":aide,
                    "id": f"ps{int(100*c.p_détour)}",
                    "longueur":g.longueur_itinéraire(iti_d),
                    "longueur_ressentie":int(l_ressentie),
                    "couleur":coul,
                    #"nom_gpx": nom_gpx,
                    "gpx": gpx_of_iti(iti_d, session, bavard=bavard-1)}
                   )


    for i, p in enumerate(ps_détour):
        c = chemins.Chemin(z_d, [d]+étapes+[a], p, False, interdites=interdites)
        coul = color_dict[ (i*n_coul)//np ]
        traite_un_chemin(c, coul, *légende_et_aide(p))
        tic = chrono(tic, f"dijkstra {c} et sa longueur")

    if ps_détour[0]==0.:
        longueur_ch_direct = res[0]["longueur"]    
    
    if rajouter_iti_direct:
        cd = chemins.Chemin(z_d, [d,a], 0, False)
        coul = "#000000"
        traite_un_chemin(cd, coul, "Trajet direct", "Le trajet le plus court, sans prendre en compte les étapes imposées.")
        tic=chrono(tic, "Calcul de l'itinéraire direct.")
        longueur_ch_direct = res[-1]["longueur"]

    # Calculer les pourcentages de détour effectifs
    if rajouter_iti_direct or ps_détour[0]==0.:
        for s in res:
            s["p_détour_effectif"] = int((s["longueur"]/longueur_ch_direct- 1.) * 100.)

    tic=perf_counter()
    dessine(à_dessiner, g, où_enregistrer=où_enregistrer, ouvrir=ouvrir, bavard=bavard, fouine="fouine" in session)
    chrono(tic, "Dessin")
    chrono(tic0, f"Total pour le chemin {c}")
    return res, c, str(d), str(a), [str(é) for é in étapes]


### création du gpx ###
# https://pypi.org/project/gpxpy/
def gpx_of_iti(iti_d, session, dossier_sortie="dijk/tmp", bavard=0):
    """
    Entrée : iti_d (Arête list)
             session (dic), le dictionnaire de la session Django

    Sortie : le gpx où les \n sont remplacés par des ν
    """
    
    res = gpxpy.gpx.GPX()
    tronçon = gpxpy.gpx.GPXTrack()
    res.tracks.append(tronçon)
    segment=gpxpy.gpx.GPXTrackSegment()
    tronçon.segments.append(segment)
    
    for a in iti_d:
        for lon,lat in a.géométrie():
            segment.points.append( gpxpy.gpx.GPXTrackPoint(lat, lon) )

    #chemin_sortie = os.path.join(dossier_sortie, nom)
    # with open(chemin_sortie , "w") as sortie:
    #     sortie.write(res.to_xml())
    #     print(f"gpx enregistré à {chemin_sortie}")
    res_str = res.to_xml().replace(" ", "%20").replace("\n","ν")
    #print(res_str)
    return res_str
    #session[nom] = res.to_xml()
    #return nom

    
#################### Affichage ####################

# Pour utiliser folium sans passer par osmnx regarder :
# https://stackoverflow.com/questions/57903223/how-to-have-colors-based-polyline-on-folium


# Affichage folium avec couleur
# voir https://stackoverflow.com/questions/56234047/osmnx-plot-a-network-on-an-interactive-web-map-with-different-colours-per-infra

def dessine(listes_chemins, g, où_enregistrer, ouvrir=False, bavard=0, fouine=False):
    """
    Entrées :
      - listes_chemins : liste de couples (liste d'Arêtes, couleur)
      - g (instance de Graphe)
      - où_enregistrer : adresse du fichier html à créer
    Effet:
      Crée le fichier html de la carte superposant tous les itinéraires fournis.
    """

    l, coul, p = listes_chemins[0]
    #sous_graphe = g.g.multidigraphe.subgraph(l)
    #carte = plot_graph_folium(sous_graphe, popup_attribute="name", color=coul)
    carte = folium_of_chemin(g, l, p, fit=True, color=coul)
    #carte = plot_route_folium(g.g.multidigraphe, l, popup_attribute="name", color=coul) # Ne marche pas...
    for l, coul, p in listes_chemins[1:]:
        #sous_graphe = g.g.multidigraphe.subgraph(l)
        #carte = plot_graph_folium(sous_graphe, popup_attribute="name", color=coul, graph_map=carte)
        carte = folium_of_chemin(g, l, p, carte=carte, color=coul)
    
    
    ajoute_marqueur(l[0].départ.coords(), carte, fouine=fouine)
    ajoute_marqueur(l[-1].arrivée.coords(), carte, fouine=fouine)
    Fullscreen(title="Plein écran", title_cancel="Quitter le plein écran").add_to(carte)
    LocateControl(locateOptions={"enableHighAccuracy":True}).add_to(carte)
    carte.save(où_enregistrer)
    if ouvrir : ouvre_html(où_enregistrer)


list_colors = [# Du vert au rouge
        "#00FF00",        "#12FF00",        "#24FF00",        "#35FF00",
        "#47FF00",        "#58FF00",        "#6AFF00",        "#7CFF00",
        "#8DFF00",        "#9FFF00",        "#B0FF00",        "#C2FF00",
        #"#D4FF00",        "#E5FF00",        #"#F7FF00",        "#FFF600",
        #"#FFE400",        "#FFD300",
        "#FFC100",        "#FFAF00",
        "#FF9E00",        "#FF8C00",        "#FF7B00",        "#FF6900",
        "#FF5700",        "#FF4600",        "#FF3400",        "#FF2300",
        "#FF1100",        "#FF0000",    ]
list_colors.reverse() # maintenant du rouge au vert
color_dict = {i: list_colors[i] for i in range(len(list_colors))}
n_coul = len(list_colors)



def dessine_chemin(c, g, où_enregistrer=os.path.join(TMP, "chemin.html"), ouvrir=False, bavard=0):
    """ 
    Entrées :
       - c (instance de Chemin)
       - g (instance de Graphe)
       - p_détour (float ou float list) : liste des autres p_détour pour lesquels lancer et afficher le calcul.
       - où_enregistrer : adresse où enregistrer le html produit.
       - ouvrir (bool) : Si True, lance le navigateur sur la page créée.

    Effet : Crée une carte html avec le chemin direct en rouge, et le chemin compte tenu de la cyclabilité en bleu.
    Sortie : Longueur du chemin, du chemin direct.
    """

    # Calcul des chemins
    c_complet, _ = dijkstra.chemin_étapes_ensembles(g, c)
    longueur = g.longueur_itinéraire(c_complet, c.p_détour)
    
    départ, arrivée = c_complet[0], c_complet[-1]
    c_direct, _ = dijkstra.chemin(g, départ, arrivée, 0)
    longueur_direct = g.longueur_itinéraire(c_direct, 0)

    dessine([(c_complet, "blue", c.p_détour), (c_direct,"red", 0)], g, où_enregistrer, ouvrir=ouvrir)
    return longueur, longueur_direct


def affiche_rue(nom_ville, rue, g, bavard=0):
    """
    Entrées : g, graphe
              
    """
    #sommets = chemins.nœud_of_étape(adresse, g, bavard=bavard-1)
    ville=normalise_ville(nom_ville)
    sommets = g.nœuds[ville.nom][normalise_rue(rue, ville)]
    affiche_sommets(sommets, g)


def moyenne(t):
    return sum(t)/len(t)


def dessine_cycla(g, z_d, où_enregistrer, bavard=0):
    """
    Entrée : où_enregistrer (str) adresse et nom du fichier à créer.
    Effet : Crée la carte de la cyclabilité.
    """

    mini, maxi = g.cycla_min[z_d], g.cycla_max[z_d] #min(g.g.cyclabilité.values()), max(g.g.cyclabilité.values())
    if bavard > 0: print(f"Valeurs extrêmes de la cyclabilité : {mini}, {maxi}")

    def num_paquet(val):
        """Renvoie un entier dans [|0, n_coul[|. 1 est associé à n_coul//2, mini à 0, maxi à 1."""

        if val==maxi:
            return n_coul-1
        elif val <= 1.:
            return int((val-mini)/(1-mini)*n_coul/2)  # dans [|0, n_coul/2 |]
        else:
            return int((val-1)/(maxi-1)*n_coul/2+n_coul/2)

    arêtes = []

    for a in mo.Arête.objects.filter(zone=z_d).exclude(cycla__isnull=True).prefetch_related("départ", "arrivée"):
        i=num_paquet(a.cycla)
        arêtes.append((a, {"color":color_dict[i], "popup":a.cycla}))

    
    
    carte = folium_of_arêtes(g, arêtes)

    carte.save(où_enregistrer)
    print(f"Carte enregistrée à {où_enregistrer}")

    
    
### Apprentissage ###

def lecture_tous_les_chemins(g, z_t=None, bavard=0):
    """
    Lance une fois l’apprentissage sur chaque chemin de la zone. Si None, parcourt toutes les zones de g.
    """
    if z_t is None:
        à_parcourir = g.zones
    else:
        à_parcourir = [Zone.objects.get(nom=z_t)]
    for z in à_parcourir:
        for c_d in Chemin_d.objects.filter(zone=z):
            c = chemins.Chemin.of_django(c_d, g , bavard=bavard-1)
            n_modif,l = ap.lecture_meilleur_chemin(g, c, bavard=bavard)
            c_d.dernier_p_modif = n_modif/l
            c_d.save()
            print(f"\nLecture de {c}. {n_modif} arêtes modifiées, distance = {l}.\n\n\n")
