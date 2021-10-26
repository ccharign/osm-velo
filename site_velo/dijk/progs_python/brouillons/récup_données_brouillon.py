# -*- coding:utf-8 -*-


#### Avec Overpass ####
import overpy
#https://towardsdatascience.com/loading-data-from-openstreetmap-with-python-and-the-overpass-api-513882a27fd0

api=overpy.Overpass()
r=api.query("""
way(38736722);out;
    """)

rue = r.ways[0]
nœuds = rue.get_nodes(resolve_missing=True)


### Avec nominatim via geopy
import geopy
geopy.geocoders.options.default_user_agent = "pau à vélo"
geolocator = geopy.geocoders.osm.Nominatim(user_agent="pau à vélo")
geoloc = geolocator.geocode("Rue Sambre et Meuse, Pau, France")
geoloc.raw["osm_id"]


### Avec nominatim à la main. https://gist.github.com/adrianespejo/5df28ce987db64ba753619502ee3d812

import json
from pprint import pprint
from typing import Dict

import requests

NOMINATIM_API_URL = "https://nominatim.openstreetmap.org"
NOMINATIM_DETAILS_ENDPOINT = f"{NOMINATIM_API_URL}/details"
NOMINATIM_SEARCH_ENDPOINT = f"{NOMINATIM_API_URL}/search"
NOMINATIM_REVERSE_ENDPOINT = f"{NOMINATIM_API_URL}/reverse"

query_params = {
    "namedetails": 1,
    "polygon_geojson": 1,
    "hierarchy": 1,
}


def fetch_osm_search(query: str, params: Dict[str, int]) -> dict:
    params_query = "&".join(f"{param_name}={param_value}" for param_name, param_value in params.items())
    request_url = f"{NOMINATIM_SEARCH_ENDPOINT}?q={query}&{params_query}&format=json"
    #print(request_url)

    response = requests.get(request_url)
    response.raise_for_status()
    return response.json()
