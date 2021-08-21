# -*- coding:utf-8 -*-

import math
from params import D_MAX_POUR_NŒUD_LE_PLUS_PROCHE

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
