# -*- coding:utf-8 -*-


#import geopandas as gpd
#import networkx as nx
import folium
#import json
from petites_fonctions import deuxConséc


# ### Recopie du plot_graph_folium de osmnx ###

# def graph_to_gdfs(G, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True):
#     """
#     Convert a MultiDiGraph to node and/or edge GeoDataFrames.

#     This function is the inverse of `graph_from_gdfs`.

#     Parameters
#     ----------
#     G : networkx.MultiDiGraph
#         input graph
#     nodes : bool
#         if True, convert graph nodes to a GeoDataFrame and return it
#     edges : bool
#         if True, convert graph edges to a GeoDataFrame and return it
#     node_geometry : bool
#         if True, create a geometry column from node x and y attributes
#     fill_edge_geometry : bool
#         if True, fill in missing edge geometry fields using nodes u and v

#     Returns
#     -------
#     geopandas.GeoDataFrame or tuple
#         gdf_nodes or gdf_edges or tuple of (gdf_nodes, gdf_edges). gdf_nodes
#         is indexed by osmid and gdf_edges is multi-indexed by u, v, key
#         following normal MultiDiGraph structure.
#     """
#     #crs = G.graph["crs"]
#     crs='epsg:4326' # C’est celui qui était dans mon graphe issu de osmnx...

#     if nodes:

#         if not G.nodes:  # pragma: no cover
#             raise ValueError("graph contains no nodes")

#         nodes, data = zip(*G.nodes(data=True))

#         if node_geometry:
#             # convert node x/y attributes to Points for geometry column
#             geom = (Point(d["x"], d["y"]) for d in data)
#             gdf_nodes = gpd.GeoDataFrame(data, index=nodes, crs=crs, geometry=list(geom))
#         else:
#             gdf_nodes = gpd.GeoDataFrame(data, index=nodes)

#         gdf_nodes.index.rename("osmid", inplace=True)
#         #utils.log("Created nodes GeoDataFrame from graph")

#     if edges:

#         if not G.edges:  # pragma: no cover
#             raise ValueError("graph contains no edges")

#         u, v, k, data = zip(*G.edges(keys=True, data=True))

#         if fill_edge_geometry:

#             # subroutine to get geometry for every edge: if edge already has
#             # geometry return it, otherwise create it using the incident nodes
#             x_lookup = nx.get_node_attributes(G, "x")
#             y_lookup = nx.get_node_attributes(G, "y")

#             def make_geom(u, v, data, x=x_lookup, y=y_lookup):
#                 if "geometry" in data:
#                     return data["geometry"]
#                 else:
#                     return LineString((Point((x[u], y[u])), Point((x[v], y[v]))))

#             geom = map(make_geom, u, v, data)
#             gdf_edges = gpd.GeoDataFrame(data, crs=crs, geometry=list(geom))

#         else:
#             gdf_edges = gpd.GeoDataFrame(data)
#             if "geometry" not in gdf_edges.columns:
#                 # if no edges have a geometry attribute, create null column
#                 gdf_edges["geometry"] = np.nan
#             gdf_edges.set_geometry("geometry")
#             gdf_edges.crs = crs

#         # add u, v, key attributes as index
#         gdf_edges["u"] = u
#         gdf_edges["v"] = v
#         gdf_edges["key"] = k
#         gdf_edges.set_index(["u", "v", "key"], inplace=True)

#         #utils.log("Created edges GeoDataFrame from graph")

#     if nodes and edges:
#         return gdf_nodes, gdf_edges
#     elif nodes:
#         return gdf_nodes
#     elif edges:
#         return gdf_edges
#     else:  # pragma: no cover
#         raise ValueError("you must request nodes or edges or both")




    
# def plot_graph_folium(
#     G,
#     graph_map=None,
#     popup_attribute=None,
#     tiles="cartodbpositron",
#     zoom=1,
#     fit_bounds=True,
#     edge_color=None,
#     edge_width=None,
#     edge_opacity=None,
#     **kwargs,
# ):
#     """
#     Plot a graph as an interactive Leaflet web map.

#     Note that anything larger than a small city can produce a large web map
#     file that is slow to render in your browser.

#     Parameters
#     ----------
#     G : networkx.MultiDiGraph
#         input graph
#     graph_map : folium.folium.Map
#         if not None, plot the graph on this preexisting folium map object
#     popup_attribute : string
#         edge attribute to display in a pop-up when an edge is clicked
#     tiles : string
#         name of a folium tileset
#     zoom : int
#         initial zoom level for the map
#     fit_bounds : bool
#         if True, fit the map to the boundaries of the graph's edges
#     kwargs
#         keyword arguments to pass to folium.PolyLine(), see folium docs for
#         options (for example `color="#333333", weight=5, opacity=0.7`)

#     Returns
#     -------
#     folium.folium.Map
#     """

#     # create gdf of all graph edges
#     gdf_edges = graph_to_gdfs(G, nodes=False)
#     return _plot_folium(gdf_edges, graph_map, popup_attribute, tiles, zoom, fit_bounds, **kwargs)


# def plot_route_folium(
#     G,
#     route,
#     route_map=None,
#     popup_attribute=None,
#     tiles="cartodbpositron",
#     zoom=1,
#     fit_bounds=True,
#     # route_color=None,
#     # route_width=None,
#     # route_opacity=None,
#     **kwargs,
# ):
#     """
#     Plot a route as an interactive Leaflet web map.

#     Parameters
#     ----------
#     G : networkx.MultiDiGraph
#         input graph
#     route : list
#         the route as a list of nodes
#     route_map : folium.folium.Map
#         if not None, plot the route on this preexisting folium map object
#     popup_attribute : string
#         edge attribute to display in a pop-up when an edge is clicked
#     tiles : string
#         name of a folium tileset
#     zoom : int
#         initial zoom level for the map
#     fit_bounds : bool
#         if True, fit the map to the boundaries of the route's edges
#     kwargs
#         keyword arguments to pass to folium.PolyLine(), see folium docs for
#         options (for example `color="#cc0000", weight=5, opacity=0.7`)

#     Returns
#     -------
#     folium.folium.Map
#     """

#     # create gdf of the route edges in order
#     node_pairs = zip(route[:-1], route[1:])
#     uvk = ((u, v, min(G[u][v], key=lambda k: G[u][v][k]["length"])) for u, v in node_pairs)
#     gdf_edges = graph_to_gdfs(G.subgraph(route), nodes=False).loc[uvk]
#     return _plot_folium(gdf_edges, route_map, popup_attribute, tiles, zoom, fit_bounds, **kwargs)


# def _plot_folium(gdf, m, popup_attribute, tiles, zoom, fit_bounds, **kwargs):
#     """
#     Plot a GeoDataFrame of LineStrings on a folium map object.

#     Parameters
#     ----------
#     gdf : geopandas.GeoDataFrame
#         a GeoDataFrame of LineString geometries and attributes
#     m : folium.folium.Map or folium.FeatureGroup
#         if not None, plot on this preexisting folium map object
#     popup_attribute : string
#         attribute to display in pop-up on-click, if None, no popup
#     tiles : string
#         name of a folium tileset
#     zoom : int
#         initial zoom level for the map
#     fit_bounds : bool
#         if True, fit the map to gdf's boundaries
#     kwargs
#         keyword arguments to pass to folium.PolyLine()

#     Returns
#     -------
#     m : folium.folium.Map
#     """

#     # get centroid
#     x, y = gdf.unary_union.centroid.xy
#     centroid = (y[0], x[0])

#     # create the folium web map if one wasn't passed-in0
#     if m is None:
#         m = folium.Map(location=centroid, zoom_start=zoom, tiles=tiles)

#     # identify the geometry and popup columns
#     if popup_attribute is None:
#         attrs = ["geometry"]
#     else:
#         attrs = ["geometry", popup_attribute]

#     # add each edge to the map
#     for vals in gdf[attrs].values:
#         params = dict(zip(["geom", "popup_val"], vals))
#         pl = _make_folium_polyline(**params, **kwargs)
#         pl.add_to(m)

#     # if fit_bounds is True, fit the map to the bounds of the route by passing
#     # list of lat-lng points as [southwest, northeast]
#     if fit_bounds and isinstance(m, folium.Map):
#         tb = gdf.total_bounds
#         m.fit_bounds([(tb[1], tb[0]), (tb[3], tb[2])])

#     return m



# def _make_folium_polyline(geom, popup_val=None, **kwargs):
#     """
#     Turn LineString geometry into a folium PolyLine with attributes.

#     Parameters
#     ----------
#     geom : shapely LineString
#         geometry of the line
#     popup_val : string
#         text to display in pop-up when a line is clicked, if None, no popup
#     kwargs
#         keyword arguments to pass to folium.PolyLine()

#     Returns
#     -------
#     pl : folium.PolyLine
#     """
#     # locations is a list of points for the polyline folium takes coords in
#     # lat,lng but geopandas provides them in lng,lat so we must reverse them
#     locations = [(lat, lng) for lng, lat in geom.coords]

#     # create popup if popup_val is not None
#     if popup_val is None:
#         popup = None
#     else:
#         # folium doesn't interpret html, so can't do newlines without iframe
#         popup = folium.Popup(html=json.dumps(popup_val))

#     # create a folium polyline with attributes
#     pl = folium.PolyLine(locations=locations, popup=popup, **kwargs)
#     return pl


def polyline_of_arête(g, a, popup=None, **kwargs):
    """
    Entrées:
        g (graphe)
        a (Arête)
        popup : texte à afficher. Si None, on prendra le nom de l’arête si disponible.
    """
    locations, nom = a.géométrie(), a.nom
    if popup is None:
        popup = nom
    loc_à_lenvers = [(lat, lon) for lon, lat in locations]
    pl = folium.PolyLine(locations=loc_à_lenvers, popup=popup, opacity=.5, **kwargs)
    return pl


def folium_of_chemin(g, iti_d, p, carte=None, tiles="cartodbpositron", zoom=1, fit=False, **kwargs):
    """
    Entrées : 
        g (graphe)
        iti_d (Arête list) : itinéraire
        carte (folium.Map)
        zoom : niveau de zoom initial
        fit : si vrai, cadre la carte avec le départ et l’arrivée de iti
        kwargs : args à passer à Polyline.
    Sortie : carte de folium.Map
    """

    #cd, cf = g.coords_of_id_osm(iti[0]), g.coords_of_id_osm(iti[-1])
    cd, cf = iti_d[0].départ.coords(), iti_d[-1].arrivée.coords() # 
    cm = (cd[0]+cf[0])/2., (cd[1]+cf[1])/2.
    
    if carte is None:
        carte = folium.Map(location=(cm[1], cm[0]), zoom_start=zoom, tiles=tiles) #Dans folium les coords sont lat, lon au lieu de lon, lat
    

    for a in iti_d:
        pl=polyline_of_arête(g, a, **kwargs)
        pl.add_to(carte)

    if fit:
        o,e = sorted([cd[0], cf[0]])#lon
        s,n = sorted([cd[1], cf[1]])#lat
        carte.fit_bounds([(s, o), (n, e)])


    return carte


def folium_of_arêtes(g, arêtes, carte=None, tiles="cartodbpositron", zoom=3):
    """
    Entrées : 
        g (graphe)
        arêtes, liste de couples (Arête, dico des args à passer à PolyLine)
        carte (folium.Map)
        zoom : niveau de zoom initial
        fit : si vrai, cadre la carte avec le départ et l’arrivée de iti
        kwargs : args à passer à Polyline. par exemple color.

    Sortie : carte de folium.Map

    Si carte est None, création d’une nouvelle carte positionnée en le premier sommet.
    """

    if len(arêtes)==0:
        # carte vide si aucune arête
        return folium.Map()
    
    if carte is None:
        lon, lat = arêtes[0][0].départ.coords()
        carte = folium.Map(location=(lat,lon), zoom_start=zoom, tiles=tiles)

    lons, lats = [], []
    for a, kwargs in arêtes:
        c1, c2 = a.départ.coords(), a.arrivée.coords()
        lons.extend((c1[0], c2[0]))
        lats.extend((c1[1], c2[1]))
        pl=polyline_of_arête(g, a, **kwargs)
        pl.add_to(carte)
    o=min(lons)
    e=max(lons)
    s=min(lats)
    n=max(lats)
    carte.fit_bounds([(s,o), (n,e)])
    return carte

    
        
def ajoute_marqueur(ad, carte, fouine=False, **kwargs):
    """
    Entrée :
        ad (Adresse)
        carte (folium.Map)
    """
    lon,lat = ad.coords
    if fouine:
        folium.Marker(location=(lat,lon), popup=str(ad), icon= folium.Icon(icon="paw", color="black", prefix="fa"), **kwargs).add_to(carte)
    else:
        folium.Marker(location=(lat,lon), popup=str(ad),**kwargs).add_to(carte)
