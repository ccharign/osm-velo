# -*- coding:utf-8 -*-



"""
Ces petites fonctions ne doivent pas dépendre d’autres modules, à part params.py, pour ne pas créer de pbde dépendance.

"""


import math
from params import D_MAX_POUR_NŒUD_LE_PLUS_PROCHE
import geopy
import time


geopy.geocoders.options.default_user_agent = "pau à vélo"
localisateur = geopy.geocoders.Nominatim(user_agent="pau à vélo")
def recherche_inversée(coords, bavard=0):
    if bavard>0:print("Pause de 1s avant la recherche inversée")
    time.sleep(1)
    return(localisateur.reverse(coords))


R_TERRE = 6378137  # en mètres

def distance_euc(c1, c2):
    """ 
    Entrée : deux coords
    Sortie : distance en mètres.
    Formule simplifiée pour petites distances."""
    long1, lat1 = c1
    long2, lat2 = c2
    dx = R_TERRE * (long2-long1) * math.pi / 180
    dy = R_TERRE * (lat2-lat1) * math.pi / 180
    return (dx**2+dy**2)**.5


def distance_si_pas_trop(c1, c2):
    d = distance_euc(c1, c2)
    if d > D_MAX_POUR_NŒUD_LE_PLUS_PROCHE:
        print(f"distance entre {c1} et {c2} supérieure à {D_MAX_POUR_NŒUD_LE_PLUS_PROCHE}")
        raise TropLoin()
    else:
        return d

def deuxConséc(t):
    """ renvoie un itérateur sur les couples d'éléments consécutifs de t."""
    n = len(t)
    for i in range(n-1):
        yield t[i], t[i+1]

        
def ajouteDico(d, clef, val):
    """d est un dico de listes.
       Ajoute val à la liste de clef donnée si pas encore présente."""
    if clef in d:
        if val not in d[clef]:
            d[clef].append(val)
    else:
            d[clef]=[val]
