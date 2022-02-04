# -*- coding:utf-8 -*-

### Fonctions diverses pour utiliser le logiciel

from time import perf_counter
from petites_fonctions import chrono, deuxConséc
import dijk.models as mo
from params import TMP
#from importlib import reload  # recharger un module après modif
import subprocess
#import networkx as nx  # graphe

#from osmnx import plot_graph_folium

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


def liste_Arête_of_iti(g, iti, p_détour):
    """
    Entrée : iti (int list), liste d'id osm
    Sortie : liste d'Arêtes
    """
    tic=perf_counter()
    res = [g.meilleure_arête(s,t,p_détour) for (s,t) in deuxConséc(iti)]
    chrono(tic, "conversion de l'itinéraire en liste d'Arêtes.")
    return res



def itinéraire(départ, arrivée, ps_détour, g, z_d,
               rajouter_iti_direct=True, noms_étapes=[], rues_interdites=[],
               où_enregistrer=os.path.join(TMP, "itinéraire.html"), bavard=0, ouvrir=False):
    """ 
    Entrées :
      - ps_détour (float list) : liste des proportion de détour pour lesquels afficher un chemin.
      - g (graphe)
      - z_d (Zone) : sert pour récupérer la ville défaut.
      - départ, arrivée : chaîne de caractère décrivant le départ et l’arrivée. Seront lues par chemins.Étape.
      - noms_étapes : liste de noms d’étapes intermédiaires. Seront également lues par chemin.Étape.

    Effet :  Crée une page html contenant l’itinéraire demandé, et l’enregistre dans où_enregistrer
             Si ouvrir est vrai, ouvre de plus un navigateur sur cette page.
    Sortie : liste de (légende, longueur, longueur ressentie, couleur) pour les itinéraires obtenus.
    """

    ## Calcul des étapes
    tic0=perf_counter()
    d = chemins.Étape(départ, g, z_d, bavard=bavard-1)
    if bavard>0:
        print(f"Départ trouvé : {d}, {d.nœuds}")
        #print(f"Voisins de {list(d.nœuds)[0]} : {list(g.voisins(list(d.nœuds)[0], .3))}")
    a = chemins.Étape(arrivée, g, z_d, bavard=bavard-1)
    if bavard>0:
        print(f"Arrivée trouvé : {a}")
    étapes = [chemins.Étape(é, g, z_d, bavard=bavard-1) for é in noms_étapes]


    ## Arêtes interdites
    interdites = chemins.arêtes_interdites(g, z_d, rues_interdites, bavard=bavard)
    tic=chrono(tic0, "Calcul des étapes et arêtes interdites.")
    
    np = len(ps_détour)
    à_dessiner = []
    res = []
    for i, p in enumerate(ps_détour):
        c = chemins.Chemin(z_d, [d]+étapes+[a], p, False, interdites=interdites)
        iti_d, l_ressentie = g.itinéraire(c, bavard=bavard-1)
        coul = color_dict[ (i*n_coul)//np ]
        à_dessiner.append( (iti_d, coul, p))
        res.append((f"Avec pourcentage détour de {100*p}",
                    g.longueur_itinéraire(iti_d), int(l_ressentie), coul )
                   )
        tic = chrono(tic, f"dijkstra {c} et sa longueur")

    if rajouter_iti_direct:
        cd = chemins.Chemin(z_d, [d,a], 0, False)
        iti_d, l_ressentie = g.itinéraire(cd, bavard=bavard-1)
        coul = "#000000"
        à_dessiner.append( (iti_d, coul, 0))
        res.append(("Itinéraire direct", g.longueur_itinéraire(iti_d), int(l_ressentie), coul ))
        tic=chrono(tic, "Calcul de l'itinéraire direct.")

    tic=perf_counter()
    dessine(à_dessiner, g, où_enregistrer=où_enregistrer, ouvrir=ouvrir, bavard=bavard)
    chrono(tic, "Dessin")
    chrono(tic0, f"Total pour l'itinéraire {c}")
    return res, c
    


    
#################### Affichage ####################

# Pour utiliser folium sans passer par osmnx regarder :
# https://stackoverflow.com/questions/57903223/how-to-have-colors-based-polyline-on-folium


# Affichage folium avec couleur
# voir https://stackoverflow.com/questions/56234047/osmnx-plot-a-network-on-an-interactive-web-map-with-different-colours-per-infra

def dessine(listes_chemins, g, où_enregistrer, ouvrir=False, bavard=0):
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
    
    
    ajoute_marqueur(l[0].départ.coords(), carte)
    ajoute_marqueur(l[-1].arrivée.coords(), carte)
    
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

    
# def dessine_chemins(chemins, g, où_enregistrer=TMP):
#     """ 
#     Affiche les chemins directs en rouge, et les chemins compte tenu de la cyclabilité en bleu.
#     Peu pertinent dès qu’il y a trop de chemins.
#     """
#     chemins_directs = []
#     for c in chemins:
#         try:
#             chemins_directs.append(c.chemin_direct_sans_cycla(g))
#         except dijkstra.PasDeChemin:
#             print(f"Pas de chemin pour {c}")
#     graphe_c_directs = g.multidigraphe.subgraph(flatten(chemins_directs))
#     carte = plot_graph_folium(graphe_c_directs, popup_attribute="name", color="red")

#     chemins_complets = []
#     for c in chemins:
#         try:
#             chemins_complets.append(dijkstra.chemin_étapes_ensembles(g, c))
#         except dijkstra.PasDeChemin as e:
#             print(e)
#             print(f"Pas de chemin avec étapes pour {c}")
#     graphe_c_complet = g.multidigraphe.subgraph(flatten(chemins_complets))
#     carte = plot_graph_folium(graphe_c_complet, popup_attribute="name", color="blue", graph_map=carte)  # On rajoute ce graphe par-dessus le précédent dans le folium
    
#     nom = os.path.join(où_enregistrer, "dessine_chemins.html")
#     carte.save(nom)
#     ouvre_html(nom)


# Ne marche plus si s n’est pas un chemin dans le graphe
# def affiche_sommets(s, g, où_enregistrer=os.path.join(TMP, "sommets"), ouvrir = True):
#     """ Entrée : s, liste de sommets """
#     dessine([(s, "blue")], g, où_enregistrer=où_enregistrer, ouvrir=ouvrir)


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


def dessine_cycla(g, z_d, où_enregistrer=TMP, bavard=0):
    """
    Crée la carte de la cyclabilité.
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

    for a in mo.Arête.objects.exclude(cycla__isnull=True).prefetch_related("départ", "arrivée"):
        i=num_paquet(a.cycla)
        #nœuds_par_cycla[i].add(s)
        #nœuds_par_cycla[i].add(t)
        arêtes.append((a, {"color":color_dict[i], "popup":a.cycla}))


    # début=True
    # for i, nœuds in enumerate(nœuds_par_cycla):
    #     if len(nœuds) > 0:
    #         print(len(nœuds))
    #         à_rajouter = g.g.multidigraphe.subgraph(list(nœuds))
    #         if début:
    #             carte = plot_graph_folium(à_rajouter, color=color_dict[i])
    #             début=False
    #         else:
    #             carte = plot_graph_folium(à_rajouter, color=color_dict[i], graph_map=carte)

    carte = folium_of_arêtes(g, arêtes)
    nom = os.path.join(où_enregistrer, "cycla.html")
    carte.save(nom)

    
### Apprentissage ###

def lecture_tous_les_chemins(g, z_d=None, bavard=0):
    """
    Lance une fois l’apprentissage sur chaque chemin de la zone. Si None, parcourt toutes les zones de g.
    """
    if z_d is None:
        à_parcourir = g.zones
    else:
        à_parcourir = [z_d]
    for z in à_parcourir:
        for c_d in Chemin_d.objects.filter(zone=z):
            c = chemins.Chemin.of_django(c_d, g , bavard=bavard-1)
            n_modif,l = ap.lecture_meilleur_chemin(g, c, bavard=bavard)
            c_d.dernier_p_modif = n_modif/l
            c_d.save()
            print(f"\nLecture de {c}. {n_modif} arêtes modifiées, distance = {l}.\n\n\n")
