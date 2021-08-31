# -*- coding:utf-8 -*-

### Fonctions diverses pour utiliser le logiciel


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
from params import NAVIGATEUR, TMP
from lecture_adresse.normalisation import VILLE_DÉFAUT, normalise_rue, normalise_ville
import os
import récup_données
import module_graphe
import webbrowser
from matplotlib import cm

def ouvre_html(chemin):
    webbrowser.open(chemin)


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


def itinéraire(départ, arrivée, p_détour, g, où_enregistrer=TMP, bavard=0):
    d = chemins.Étape(départ, g)
    a = chemins.Étape(arrivée, g)
    c = chemins.Chemin([d, a], p_détour, False)
    res = g.chemin_étapes_ensembles(c)
    graphe_c = g.multidigraphe.subgraph(res)
    carte = ox.plot_graph_folium(graphe_c, popup_attribute="name")
    nom = os.path.join(où_enregistrer, (départ+arrivée).replace(" ","")+".html")
    carte.save(nom)
    ouvre_html(nom)
    #ox.plot_route_folium(g.multidigraphe,c)


    
#################### Affichage ####################



# Affichage folium avec couleur
# voir https://stackoverflow.com/questions/56234047/osmnx-plot-a-network-on-an-interactive-web-map-with-different-colours-per-infra


def flatten(c):
    res = []
    for x in c:
        res.extend(x)
    return res



def dessine_chemin(c, g, où_enregistrer=TMP):
    """ Affiche les chemins directs en rouge, et les chemins compte tenu de la cyclabilité en bleu."""
    assert isinstance(c, chemins.Chemin)

    c_complet = dijkstra.chemin_étapes_ensembles(g, c)
    départ, arrivée = c_complet[0], c_complet[-1]
    
    c_direct = dijkstra.chemin(g,départ,arrivée,0)
    graphe_c_direct = g.multidigraphe.subgraph(c_direct)
    carte = ox.plot_graph_folium(graphe_c_direct, popup_attribute="name", color="red")

    
    graphe_c_complet = g.multidigraphe.subgraph(c_complet)
    carte = ox.plot_graph_folium(graphe_c_complet, popup_attribute="name", color="blue", graph_map=carte)  # On rajoute ce graphe par-dessus le précédent dans le folium
    
    nom = os.path.join(où_enregistrer, c.texte_court())
    carte.save(nom)
    ouvre_html(nom)


def dessine_chemins(chemins, g, où_enregistrer=TMP):
    """ Affiche les chemins directs en rouge, et les chemins compte tenu de la cyclabilité en bleu."""
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
    
    nom = os.path.join(où_enregistrer, "dessine_chemins.html")
    carte.save(nom)
    ouvre_html(nom)


def affiche_sommets(s, g, où_enregistrer=TMP):
    """ Entrée : s, liste de sommets """
    graphe_c = g.multidigraphe.subgraph(s)
    carte = ox.plot_graph_folium(graphe_c, popup_attribute="name")
    nom = os.path.join(où_enregistrer, "affiche_sommets.html")
    carte.save(nom)
    ouvre_html(nom)


def affiche_rue(ville, rue, g, bavard=0):
    """
    Entrées : g, graphe
              
    """
    #sommets = chemins.nœud_of_étape(adresse, g, bavard=bavard-1)
    sommets = g.nœuds[str(normalise_ville(ville))][normalise_rue(rue)]
    affiche_sommets(sommets, g)


# Pour utiliser folium sans passer par osmnx regarder :
# https://stackoverflow.com/questions/57903223/how-to-have-colors-based-polyline-on-folium
def dessine_cycla(g, où_enregistrer=TMP, bavard=0 ):
   
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

        

    nœuds_par_cycla = [ set([]) for i in range(n_coul)]
    

    for s in g.digraphe.nodes:
        for t in g.voisins_nus(s):
            if (s,t) in g.cyclabilité:
                i=num_paquet(g.cyclabilité[(s,t)])
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
        
    nom = os.path.join(où_enregistrer, "cycla.html")
    carte.save(nom)
    ouvre_html(nom)
