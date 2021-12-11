# -*- coding:utf-8 -*-

### Fonctions diverses pour utiliser le logiciel

from params import TMP
from importlib import reload  # recharger un module après modif
import subprocess
#import networkx as nx  # graphe
from osmnx import plot_graph_folium
#ox.config(use_cache=True, log_console=True)
#from module_graphe import graphe  #ma classe de graphe
#import récup_données as rd
#import apprentissage
import dijkstra
import chemins  # classe chemin et lecture du csv

from lecture_adresse.normalisation import VILLE_DÉFAUT, normalise_rue, normalise_ville
import os
#import recup_donnees
#import module_graphe
import webbrowser
#from matplotlib import cm
import folium
import geopandas as gpd

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
               où_enregistrer=os.path.join(TMP, "itinéraire.html"), bavard=0, ouvrir=False):
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
    d = chemins.Étape(départ, g, bavard=bavard-1)
    if bavard>0:
        print(f"Départ trouvé : {d}, {d.nœuds}")
        #print(f"Voisins de {list(d.nœuds)[0]} : {list(g.voisins(list(d.nœuds)[0], .3))}")
    a = chemins.Étape(arrivée, g, bavard=bavard-1)
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
        cd = chemins.Chemin([d,a], 0, False)
        iti, l_ressentie = dijkstra.chemin_étapes_ensembles(g, cd, bavard=bavard-1)
        coul = "#000000"
        à_dessiner.append( (iti, coul))
        res.append(("Itinéraire direct", g.longueur_itinéraire(iti), int(l_ressentie), coul ))

        
    dessine(à_dessiner, g, où_enregistrer=où_enregistrer, ouvrir=ouvrir, bavard=bavard)
    return res, c
    


    
#################### Affichage ####################

# Pour utiliser folium sans passer par osmnx regarder :
# https://stackoverflow.com/questions/57903223/how-to-have-colors-based-polyline-on-folium


# Affichage folium avec couleur
# voir https://stackoverflow.com/questions/56234047/osmnx-plot-a-network-on-an-interactive-web-map-with-different-colours-per-infra

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
    sous_graphe = g.g.multidigraphe.subgraph(l)
    carte = plot_graph_folium(sous_graphe, popup_attribute="name", color=coul)
    for l, coul in listes_sommets[1:]:
        sous_graphe = g.g.multidigraphe.subgraph(l)
        carte = plot_graph_folium(sous_graphe, popup_attribute="name", color=coul, graph_map=carte)
    
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
    carte = plot_graph_folium(graphe_c_directs, popup_attribute="name", color="red")

    chemins_complets = []
    for c in chemins:
        try:
            chemins_complets.append(dijkstra.chemin_étapes_ensembles(g, c))
        except dijkstra.PasDeChemin as e:
            print(e)
            print(f"Pas de chemin avec étapes pour {c}")
    graphe_c_complet = g.multidigraphe.subgraph(flatten(chemins_complets))
    carte = plot_graph_folium(graphe_c_complet, popup_attribute="name", color="blue", graph_map=carte)  # On rajoute ce graphe par-dessus le précédent dans le folium
    
    nom = os.path.join(où_enregistrer, "dessine_chemins.html")
    carte.save(nom)
    ouvre_html(nom)


def affiche_sommets(s, g, où_enregistrer=os.path.join(TMP, "sommets"), ouvrir = True):
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
   
    mini, maxi = min(g.g.cyclabilité.values()), max(g.g.cyclabilité.values())
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
    

    for s in g.g.digraphe.nodes:
        for t in g.voisins_nus(s):
            vals=[]
            if (s,t) in g.g.cyclabilité:
                vals.append(g.g.cyclabilité[(s,t)])
            if (t,s) in g.g.cyclabilité:
                vals.append(g.g.cyclabilité[(t,s)])
            if len(vals)>0:
                i=num_paquet(moyenne(vals))
                nœuds_par_cycla[i].add(s)
                nœuds_par_cycla[i].add(t)


    début=True
    for i, nœuds in enumerate(nœuds_par_cycla):
        if len(nœuds) > 0:
            print(len(nœuds))
            à_rajouter = g.g.multidigraphe.subgraph(list(nœuds))
            if début:
                carte = plot_graph_folium(à_rajouter, color=color_dict[i])
                début=False
            else:
                carte = plot_graph_folium(à_rajouter, color=color_dict[i], graph_map=carte)
        
    nom = os.path.join(où_enregistrer, "cycla.html")
    carte.save(nom)
    if ouvrir : ouvre_html(nom)


### Recopie du plot_graph_folium de osmnx ###



def graph_to_gdfs(G, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True):
    """
    Convert a MultiDiGraph to node and/or edge GeoDataFrames.

    This function is the inverse of `graph_from_gdfs`.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph
    nodes : bool
        if True, convert graph nodes to a GeoDataFrame and return it
    edges : bool
        if True, convert graph edges to a GeoDataFrame and return it
    node_geometry : bool
        if True, create a geometry column from node x and y attributes
    fill_edge_geometry : bool
        if True, fill in missing edge geometry fields using nodes u and v

    Returns
    -------
    geopandas.GeoDataFrame or tuple
        gdf_nodes or gdf_edges or tuple of (gdf_nodes, gdf_edges). gdf_nodes
        is indexed by osmid and gdf_edges is multi-indexed by u, v, key
        following normal MultiDiGraph structure.
    """
    #crs = G.graph["crs"]
    crs='epsg:4326' # C’est celui qui était dans mon graphe issu de osmnx...

    if nodes:

        if not G.nodes:  # pragma: no cover
            raise ValueError("graph contains no nodes")

        nodes, data = zip(*G.nodes(data=True))

        if node_geometry:
            # convert node x/y attributes to Points for geometry column
            geom = (Point(d["x"], d["y"]) for d in data)
            gdf_nodes = gpd.GeoDataFrame(data, index=nodes, crs=crs, geometry=list(geom))
        else:
            gdf_nodes = gpd.GeoDataFrame(data, index=nodes)

        gdf_nodes.index.rename("osmid", inplace=True)
        utils.log("Created nodes GeoDataFrame from graph")

    if edges:

        if not G.edges:  # pragma: no cover
            raise ValueError("graph contains no edges")

        u, v, k, data = zip(*G.edges(keys=True, data=True))

        if fill_edge_geometry:

            # subroutine to get geometry for every edge: if edge already has
            # geometry return it, otherwise create it using the incident nodes
            x_lookup = nx.get_node_attributes(G, "x")
            y_lookup = nx.get_node_attributes(G, "y")

            def make_geom(u, v, data, x=x_lookup, y=y_lookup):
                if "geometry" in data:
                    return data["geometry"]
                else:
                    return LineString((Point((x[u], y[u])), Point((x[v], y[v]))))

            geom = map(make_geom, u, v, data)
            gdf_edges = gpd.GeoDataFrame(data, crs=crs, geometry=list(geom))

        else:
            gdf_edges = gpd.GeoDataFrame(data)
            if "geometry" not in gdf_edges.columns:
                # if no edges have a geometry attribute, create null column
                gdf_edges["geometry"] = np.nan
            gdf_edges.set_geometry("geometry")
            gdf_edges.crs = crs

        # add u, v, key attributes as index
        gdf_edges["u"] = u
        gdf_edges["v"] = v
        gdf_edges["key"] = k
        gdf_edges.set_index(["u", "v", "key"], inplace=True)

        utils.log("Created edges GeoDataFrame from graph")

    if nodes and edges:
        return gdf_nodes, gdf_edges
    elif nodes:
        return gdf_nodes
    elif edges:
        return gdf_edges
    else:  # pragma: no cover
        raise ValueError("you must request nodes or edges or both")




    
def plot_graph_folium(
    G,
    graph_map=None,
    popup_attribute=None,
    tiles="cartodbpositron",
    zoom=1,
    fit_bounds=True,
    edge_color=None,
    edge_width=None,
    edge_opacity=None,
    **kwargs,
):
    """
    Plot a graph as an interactive Leaflet web map.

    Note that anything larger than a small city can produce a large web map
    file that is slow to render in your browser.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph
    graph_map : folium.folium.Map
        if not None, plot the graph on this preexisting folium map object
    popup_attribute : string
        edge attribute to display in a pop-up when an edge is clicked
    tiles : string
        name of a folium tileset
    zoom : int
        initial zoom level for the map
    fit_bounds : bool
        if True, fit the map to the boundaries of the graph's edges
    kwargs
        keyword arguments to pass to folium.PolyLine(), see folium docs for
        options (for example `color="#333333", weight=5, opacity=0.7`)

    Returns
    -------
    folium.folium.Map
    """

    # create gdf of all graph edges
    gdf_edges = utils_graph.graph_to_gdfs(G, nodes=False)
    return _plot_folium(gdf_edges, graph_map, popup_attribute, tiles, zoom, fit_bounds, **kwargs)


def plot_route_folium(
    G,
    route,
    route_map=None,
    popup_attribute=None,
    tiles="cartodbpositron",
    zoom=1,
    fit_bounds=True,
    route_color=None,
    route_width=None,
    route_opacity=None,
    **kwargs,
):
    """
    Plot a route as an interactive Leaflet web map.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph
    route : list
        the route as a list of nodes
    route_map : folium.folium.Map
        if not None, plot the route on this preexisting folium map object
    popup_attribute : string
        edge attribute to display in a pop-up when an edge is clicked
    tiles : string
        name of a folium tileset
    zoom : int
        initial zoom level for the map
    fit_bounds : bool
        if True, fit the map to the boundaries of the route's edges
    kwargs
        keyword arguments to pass to folium.PolyLine(), see folium docs for
        options (for example `color="#cc0000", weight=5, opacity=0.7`)

    Returns
    -------
    folium.folium.Map
    """

    # create gdf of the route edges in order
    node_pairs = zip(route[:-1], route[1:])
    uvk = ((u, v, min(G[u][v], key=lambda k: G[u][v][k]["length"])) for u, v in node_pairs)
    gdf_edges = utils_graph.graph_to_gdfs(G.subgraph(route), nodes=False).loc[uvk]
    return _plot_folium(gdf_edges, route_map, popup_attribute, tiles, zoom, fit_bounds, **kwargs)


def _plot_folium(gdf, m, popup_attribute, tiles, zoom, fit_bounds, **kwargs):
    """
    Plot a GeoDataFrame of LineStrings on a folium map object.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        a GeoDataFrame of LineString geometries and attributes
    m : folium.folium.Map or folium.FeatureGroup
        if not None, plot on this preexisting folium map object
    popup_attribute : string
        attribute to display in pop-up on-click, if None, no popup
    tiles : string
        name of a folium tileset
    zoom : int
        initial zoom level for the map
    fit_bounds : bool
        if True, fit the map to gdf's boundaries
    kwargs
        keyword arguments to pass to folium.PolyLine()

    Returns
    -------
    m : folium.folium.Map
    """
    # check if we were able to import folium successfully
    if folium is None:  # pragma: no cover
        raise ImportError("folium must be installed to use this optional feature")

    # get centroid
    x, y = gdf.unary_union.centroid.xy
    centroid = (y[0], x[0])

    # create the folium web map if one wasn't passed-in
    if m is None:
        m = folium.Map(location=centroid, zoom_start=zoom, tiles=tiles)

    # identify the geometry and popup columns
    if popup_attribute is None:
        attrs = ["geometry"]
    else:
        attrs = ["geometry", popup_attribute]

    # add each edge to the map
    for vals in gdf[attrs].values:
        params = dict(zip(["geom", "popup_val"], vals))
        pl = _make_folium_polyline(**params, **kwargs)
        pl.add_to(m)

    # if fit_bounds is True, fit the map to the bounds of the route by passing
    # list of lat-lng points as [southwest, northeast]
    if fit_bounds and isinstance(m, folium.Map):
        tb = gdf.total_bounds
        m.fit_bounds([(tb[1], tb[0]), (tb[3], tb[2])])

    return m
