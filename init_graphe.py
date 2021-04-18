# -*- coding:utf-8 -*-


import networkx as nx
import osmnx as ox
ox.config(use_cache=True, log_console=True)
from module_graphe import graphe #ma classe de graphe


# Pour la simplification dans osmnx :
# https://github.com/gboeing/osmnx-examples/blob/master/notebooks/04-simplify-graph-consolidate-nodes.ipynb

# filtrage
# https://stackoverflow.com/questions/63466207/how-to-create-a-filtered-graph-from-an-osm-formatted-xml-file-using-osmnx


def charge_graphe(zone = "Pau, France", option={"network_type":"all"}, bavard=0):
    try:
        g= ox.io.load_graphml(f'données/{zone}.graphml')
        if bavard:print("Graphe en mémoire !")
    except FileNotFoundError:
        if bavard:print("Graphe pas en mémoire. Chargement depuis osm.")
        g=ox.graph_from_place(zone, **option)
        if bavard:print("Chargement fini. Je l'enregistr pour la prochaie fois.")
        ox.io.save_graphml(g, f"données/{zone}.graphml")
    
    gr = graphe(g)
    gr.charge_cache() # nœud_of_rue
    return gr


## brouillon
"""
g = ox.graph_from_place("Pau, France", network_type="all", simplify=False)
G_proj = ox.project_graph(g)
intersections = ox.consolidate_intersections(
    G_proj, rebuild_graph=False, tolerance=10, dead_ends=False
)
G_simp = ox.consolidate_intersections(G_proj, rebuild_graph=True, tolerance=10, dead_ends=True) # perd la géométrie des arêtes


nc = ["r" if ox.simplification._is_endpoint(g, node) else "y" for node in g.nodes()]
ox.plot_graph(g, node_color=nc)
nc = ["r" if ox.simplification._is_endpoint(g, node, strict=False) else "y" for node in g.nodes()]
fig, ax = ox.plot_graph(g, node_color=nc)
"""
