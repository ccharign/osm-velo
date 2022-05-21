# -*- coding:utf-8 -*-


#import geopandas as gpd
#import networkx as nx
import folium
#import json
from petites_fonctions import deuxConséc

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


def couleur_of_cycla(a, g, z_d):
    """Renvoie un entier dans [|0, n_coul[|. 1 est associé à n_coul//2, mini à 0, maxi à 1."""
    val=a.cyclabilité()
    mini, maxi = g.cycla_min[z_d], g.cycla_max[z_d] #min(g.g.cyclabilité.values()), max(g.g.cyclabilité.values())
    if val==maxi:
        i= n_coul-1
    elif val <= 1.:
        i= int((val-mini)/(1-mini)*n_coul/2)  # dans [|0, n_coul/2 |]
    else:
        i= int((val-1)/(maxi-1)*n_coul/2+n_coul/2)
    return color_dict[i]


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


def folium_of_chemin(g, z_d, iti_d, p, carte=None, tiles="cartodbpositron", zoom=1, fit=False, **kwargs):
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
        if "color" in kwargs:
            kwargs.pop("color")
        pl=polyline_of_arête(g, a, color=couleur_of_cycla(a, g, z_d),  **kwargs)
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
