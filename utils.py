# -*- coding:utf-8 -*-

### Fonctions diverses pour utiliser le logiciel


from importlib import reload # recharger un module après modif
import subprocess
import networkx as nx # graphe
import osmnx as ox
ox.config(use_cache=True, log_console=True)


from module_graphe import graphe #ma classe de graphe
from init_graphe import g # le graphe de Pau par défaut
#import récup_données as rd
import apprentissage
import dijkstra
import chemins # classe chemin et lecture du csv



def dessine_chemins(chemins, g):

    chemins_directs=[]
    for c in chemins:
        try:
            chemins_directs.append( dijkstra.chemin(g, c.départ(), c.arrivée(), c.p_détour))
        except dijkstra.PasDeChemin:
            print(f"Pas de chemin pour {c}")

    chemins_complets=[]
    for c in chemins:
        try:
            chemins_complets.append( dijkstra.chemin_étapes(g, c) )
        except dijkstra.PasDeChemin as e :
            print(e)
            print(f"Pas de chemin avec étapes pour {c}")
            
    #chemins_complets = [ dijkstra.chemin_étapes(g, c) for c in chemins ]
    g.affiche_chemins(chemins_directs+chemins_complets )


def cheminsValides(chemins):
    """ Renvoie les chemins pour lesquels dijkstra.chemin_étapes a fonctionné sans erreur."""
    res=[]
    for c in chemins:
        try:
            dijkstra.chemin_étapes(g, c)
            res.append(c)
        except dijkstra.PasDeChemin as e :
            print(e)
            print(f"Pas de chemin avec étapes pour {c}")
    return res



def itinéraire(départ, arrivée, p_détour, où_enregistrer="tmp", g=g):
    rd, vd = chemins.lecture_étape(départ)
    ra, va = chemins.lecture_étape(arrivée)
    id_d = g.un_nœud_sur_rue(rd, ville = vd)
    id_a = g.un_nœud_sur_rue(ra, ville = va)
    c = g.chemin(id_d, id_a, p_détour)
    graphe_c = g.multidigraphe.subgraph(c)
    carte = ox.plot_graph_folium(graphe_c, popup_attribute="name")
    nom = os.path.join(où_enregistrer, départ+arrivée+".html")
    carte.save(nom)
    subprocess.run(["firefox", nom])
    #ox.plot_route_folium(g.multidigraphe,c)



def itinéraire(départ, arrivée, p_détour, où_enregistrer="tmp", g=g):
    id_d = g.nœud_centre_rue(départ)
    id_a = g.nœud_centre_rue(arrivée)
    c = g.chemin(id_d, id_a, p_détour)
    graphe_c = g.multidigraphe.subgraph(c)
    carte = ox.plot_graph_folium(graphe_c, popup_attribute="name")
    nom = os.path.join(où_enregistrer, départ+arrivée+".html")
    carte.save(nom)
    subprocess.run([NAVIGATEUR, nom])
    #ox.plot_route_folium(g.multidigraphe,c)



### Affichage folium avec couleur
# voir https://stackoverflow.com/questions/56234047/osmnx-plot-a-network-on-an-interactive-web-map-with-different-colours-per-infra


def flatten(c):
    res=[]
    for x in c:
        res.extend(x)
    return res


def dessine_chemins(chemins, g, où_enregistrer="tmp"):

    chemins_directs=[]
    for c in chemins:
        try:
            chemins_directs.append( dijkstra.chemin(g, c.départ(), c.arrivée(), c.p_détour))
        except dijkstra.PasDeChemin:
            print(f"Pas de chemin pour {c}")
    graphe_c_directs = g.multidigraphe.subgraph(flatten(chemins_directs))
    carte = ox.plot_graph_folium(graphe_c_directs, popup_attribute="name", color = "red")
    

    chemins_complets=[]
    for c in chemins:
        try:
            chemins_complets.append( dijkstra.chemin_étapes(g, c) )
        except dijkstra.PasDeChemin as e :
            print(e)
            print(f"Pas de chemin avec étapes pour {c}")
    graphe_c_complets = g.multidigraphe.subgraph(flatten(chemins_conplets))
    carte = ox.plot_graph_folium(graphe_c_complet, popup_attribute="name", color="blue", graph_map=carte) # On rajoute ce graphe par-dessus le précédent dans le folium
            
    nom = os.path.join(où_enregistrer, "dessine_chemins.html")
    carte.save(nom)
    subprocess.run([NAVIGATEUR, nom])



def affiche_sommets(s, où_enregistrer="tmp", g=g):
    """ Entrée : s, liste de sommets """
    graphe_c = g.multidigraphe.subgraph(s)
    carte = ox.plot_graph_folium(graphe_c, popup_attribute="name")
    nom = os.path.join(où_enregistrer, "affiche_sommets.html")
    carte.save(nom)
    subprocess.run(["firefox", nom])

def affiche_rue(nom_rue, ville=VILLE_DÉFAUT):
    sommets = récup_données.nœuds_sur_rue_local(nom_rue, ville=ville, pays="France", bavard=0)
    affiche_sommets(sommets)
