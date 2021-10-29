# -*- coding:utf-8 -*-

### Fonctions diverses pour utiliser le logiciel

from params import TMP
from importlib import reload  # recharger un module après modif
import subprocess
import networkx as nx  # graphe
import osmnx as ox
ox.config(use_cache=True, log_console=True)
from module_graphe import graphe  #ma classe de graphe
#import récup_données as rd
import apprentissage
import dijkstra
import chemins  # classe chemin et lecture du csv

from lecture_adresse.normalisation import VILLE_DÉFAUT, normalise_rue, normalise_ville
import os
import recup_donnees
#import module_graphe
import webbrowser
from matplotlib import cm
import folium

def flatten(c):
    """ Ne sert que pour dessine_chemins qui lui même ne sert presque à rien."""
    res = []
    for x in c:
        res.extend(x)
    return res


def ouvre_html(fichier):
    webbrowser.open(fichier)


def cheminsValides(chemins, g):
    """ Renvoie les chemins pour lesquels dijkstra.chemin_étapes a fonctionné sans erreur."""
    res = []
    for c in chemins:
        try:
            dijkstra.chemin_étapes_ensembles(g, c)
            res.append(c)
        except dijkstra.PasDeChemin as e:
            print(e)
            print(f"Pas de chemin avec étapes pour {c}")
    return res


def itinéraire(départ, arrivée, ps_détour, g,
               rajouter_iti_direct=True, noms_étapes=[], rues_interdites=[],
               où_enregistrer=os.path.join(TMP, "itinéraire.html".encode("utf-8")), bavard=0, ouvrir=False):
    """ 
    Entrées :
      - ps_détour (float list) : liste des proportion de détour pour lesquels afficher un chemin.
      - départ, arrivée : chaîne de caractère décrivant le départ et l’arrivée. Seront lues par chemins.Étape.
      - noms_étapes : liste de noms d’étapes intermédiaires. Seront également lues par chemin.Étape.

    Effet :  Crée une page html contenant l’itinéraire demandé, et l’enregistre dans où_enregistrer
             Si ouvrir est vrai, ouvre de plus un navigateur sur cette page.
    Sortie : liste de (légend, longeur, longueur ressentie, couleur) pour les itinéraires obtenus
    """

    ## Calcul des étapes
    d = chemins.Étape(départ, g)
    if bavard>0:
        print(f"Départ trouvé : {d}, {d.nœuds}")
        #print(f"Voisins de {list(d.nœuds)[0]} : {list(g.voisins(list(d.nœuds)[0], .3))}")
    a = chemins.Étape(arrivée, g)
    if bavard>0:
        print(f"Arrivée trouvé : {a}")
    étapes = [chemins.Étape(é, g) for é in noms_étapes]


    ## Arêtes interdites
    interdites = chemins.arêtes_interdites(g, rues_interdites, bavard=bavard)

    

    np = len(ps_détour)
    à_dessiner = []
    res = []
    for i, p in enumerate(ps_détour):
        c = chemins.Chemin([d]+étapes+[a], p, False, interdites=interdites)
        iti, l_ressentie = dijkstra.chemin_étapes_ensembles(g, c, bavard=bavard-1)
        if bavard>1:print(iti)
        coul = color_dict[ (i*n_coul)//np ]
        à_dessiner.append( (iti, coul))
        res.append((f"Avec pourcentage détour de {100*p}", g.longueur_itinéraire(iti), int(l_ressentie), coul ))

    if rajouter_iti_direct:
        c = chemins.Chemin([d,a], 0, False)
        iti, l_ressentie = dijkstra.chemin_étapes_ensembles(g, c, bavard=bavard-1)
        coul = "#000000"
        à_dessiner.append( (iti, coul))
        res.append(("Itinéraire direct", g.longueur_itinéraire(iti), int(l_ressentie), coul ))

        
    dessine(à_dessiner, g, où_enregistrer=où_enregistrer, ouvrir=ouvrir, bavard=bavard)
    return res
    


    
#################### Affichage ####################

# Pour utiliser folium sans passer par osmnx regarder :
# https://stackoverflow.com/questions/57903223/how-to-have-colors-based-polyline-on-folium


# Affichage folium avec couleur
# voir https://stackoverflow.com/questions/56234047/osmnx-plot-a-network-on-an-interactive-web-map-with-different-colours-per-infra

# Gestion de plusieurs p_détour ?
# arg facultatif autres_p_détour

def dessine(listes_sommets, g, où_enregistrer, ouvrir=False, bavard=0):
    """
    Entrées :
      - listes_sommets : liste de couples (liste de sommets, couleur)
      - g (instance de Graphe)
      - où_enregistrer : adresse du fichier html à créer
    Effet:
      Crée le fichier html de la carte superposant tous les itinéraires fournis.
    """

    l, coul = listes_sommets[0]
    sous_graphe = g.multidigraphe.subgraph(l)
    carte = ox.plot_graph_folium(sous_graphe, popup_attribute="name", color=coul)
    for l, coul in listes_sommets[1:]:
        sous_graphe = g.multidigraphe.subgraph(l)
        carte = ox.plot_graph_folium(sous_graphe, popup_attribute="name", color=coul, graph_map=carte)
    
    carte.save(où_enregistrer)
    print(g.coords_of_nœud(l[0]))
    folium.CircleMarker(location=g.coords_of_nœud(l[0])).add_to(carte)
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



def dessine_chemin(c, g, où_enregistrer=os.path.join(TMP, "chemin.html".encode("utf-8")), ouvrir=False, bavard=0):
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
    longueur = g.longueur_itinéraire(c_complet)
    
    départ, arrivée = c_complet[0], c_complet[-1]
    c_direct, _ = dijkstra.chemin(g, départ, arrivée, 0)
    longueur_direct = g.longueur_itinéraire(c_direct)

    dessine([(c_complet, "blue"), (c_direct,"red")], g, où_enregistrer, ouvrir=ouvrir)
    return longueur, longueur_direct

    
def dessine_chemins(chemins, g, où_enregistrer=TMP):
    """ 
    Affiche les chemins directs en rouge, et les chemins compte tenu de la cyclabilité en bleu.
    Peu pertinent dès qu’il y a trop de chemins.
    """
    chemins_directs = []
    for c in chemins:
        try:
            chemins_directs.append(c.chemin_direct_sans_cycla(g))
        except dijkstra.PasDeChemin:
            print(f"Pas de chemin pour {c}")
    graphe_c_directs = g.multidigraphe.subgraph(flatten(chemins_directs))
    carte = ox.plot_graph_folium(graphe_c_directs, popup_attribute="name", color="red")

    chemins_complets = []
    for c in chemins:
        try:
            chemins_complets.append(dijkstra.chemin_étapes_ensembles(g, c))
        except dijkstra.PasDeChemin as e:
            print(e)
            print(f"Pas de chemin avec étapes pour {c}")
    graphe_c_complet = g.multidigraphe.subgraph(flatten(chemins_complets))
    carte = ox.plot_graph_folium(graphe_c_complet, popup_attribute="name", color="blue", graph_map=carte)  # On rajoute ce graphe par-dessus le précédent dans le folium
    
    nom = os.path.join(où_enregistrer, "dessine_chemins.html".encode("utf-8"))
    carte.save(nom)
    ouvre_html(nom)


def affiche_sommets(s, g, où_enregistrer=os.path.join(TMP, "sommets".encode("utf-8")), ouvrir = True):
    """ Entrée : s, liste de sommets """
    dessine([(s, "blue")], g, où_enregistrer=où_enregistrer, ouvrir=ouvrir)


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

def dessine_cycla(g, où_enregistrer=TMP, bavard=0, ouvrir=False ):
    """
    Crée la carte de la cyclabilité.
    """
   
    mini, maxi = min(g.cyclabilité.values()), max(g.cyclabilité.values())
    if bavard > 0: print(f"Valeurs extrêmes de la cyclabilité : {mini}, {maxi}")
    
    def num_paquet(val):
        """Renvoie un entier dans [|0, n_coul[|. 1 est associé à n_coul//2, mini à 0, maxi à 1."""

        if val==maxi:
            return n_coul-1
        elif val <= 1.:
            return int((val-mini)/(1-mini)*n_coul/2)  # dans [|0, n_coul/2 |]
        else:
            return int((val-1)/(maxi-1)*n_coul/2+n_coul/2)

        

    nœuds_par_cycla = [ set() for i in range(n_coul)]
    

    for s in g.digraphe.nodes:
        for t in g.voisins_nus(s):
            vals=[]
            if (s,t) in g.cyclabilité:
                vals.append(g.cyclabilité[(s,t)])
            if (t,s) in g.cyclabilité:
                vals.append(g.cyclabilité[(t,s)])
            if len(vals)>0:
                i=num_paquet(moyenne(vals))
                nœuds_par_cycla[i].add(s)
                nœuds_par_cycla[i].add(t)


    début=True
    for i, nœuds in enumerate(nœuds_par_cycla):
        if len(nœuds) > 0:
            print(len(nœuds))
            à_rajouter = g.multidigraphe.subgraph(list(nœuds))
            if début:
                carte = ox.plot_graph_folium(à_rajouter, color=color_dict[i])
                début=False
            else:
                carte = ox.plot_graph_folium(à_rajouter, color=color_dict[i], graph_map=carte)
        
    nom = os.path.join(où_enregistrer.encode("utf-8"), "cycla.html".encode("utf-8"))
    carte.save(nom)
    if ouvrir : ouvre_html(nom)


