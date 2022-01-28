# -*- coding:utf-8 -*-



"""
Ces petites fonctions ne doivent pas dépendre d’autres modules, à part params.py, pour ne pas créer de pb de dépendance.

"""


from math import pi, cos
from params import D_MAX_POUR_NŒUD_LE_PLUS_PROCHE, LOG
import geopy
import time
import shutil
import os
import datetime


def sauv_fichier(chemin):
    """
    Crée une copie du fichier dans le sous-répertoire « sauv » du répertoire contenant le fichier. Le sous-répertoire « sauv » doit exister au préalable.
    """
    dossier, nom = os.path.split(chemin)
    dossier_sauv = os.path.join(dossier,"sauv")
    os.makedirs(dossier_sauv, exist_ok=True)
    nom_sauv = nom+str(datetime.datetime.now())
    shutil.copyfile(
        chemin,
        os.path.join(dossier_sauv, nom_sauv)
    )

geopy.geocoders.options.default_user_agent = "pau à vélo"
localisateur = geopy.geocoders.Nominatim(user_agent="pau à vélo")
def recherche_inversée(coords, bavard=0):
    if bavard>0:print("Pause de 1s avant la recherche inversée")
    time.sleep(1)
    return(localisateur.reverse(coords))


R_TERRE = 6360000  # en mètres

def distance_euc(c1, c2):
    """ 
    Entrée : deux coords
    Sortie : distance en mètres.
    Formule simplifiée pour petites distances."""
    long1, lat1 = c1
    long2, lat2 = c2
    #assert lat1>40 and lat2>40, f"Je voulais des coordonnées au format (lon, lat) et j’ai reçu {c1} et {c2}"
    dx = R_TERRE * cos(lat1) * (long2-long1) * pi / 180
    dy = R_TERRE * (lat2-lat1) * pi / 180
    # vraie formule : arccos(cos(lat1)cos(lat2)cos(lon2-lon1) + sin(lat1 lat2))
    return (dx**2+dy**2)**.5



def distance_si_pas_trop(c1, c2):
    d = distance_euc(c1, c2)
    if d > D_MAX_POUR_NŒUD_LE_PLUS_PROCHE:
        print(f"distance entre {c1} et {c2} supérieure à {D_MAX_POUR_NŒUD_LE_PLUS_PROCHE}")
        raise TropLoin()
    else:
        return d

def deuxConséc(t):
    """ Renvoie un itérateur sur les couples d'éléments consécutifs de t."""
    n = len(t)
    for i in range(n-1):
        yield t[i], t[i+1]

def union(t1, t2):
    """
    Entrée : t1, t2 deux itérateur
    Sortie : itérateur sur t1 ∪ t2
    """
    for x in t1:
        yield x
    for x in t2:
        yield x
        
def ajouteDico(d, clef, val):
    """d est un dico de listes.
       Ajoute val à la liste de clef donnée si pas encore présente."""
    if clef in d:
        if val not in d[clef]:
            d[clef].append(val)
    else:
            d[clef]=[val]

def chrono(tic, tâche, bavard=1, force=False):
    """
    Entrée : tic, float
             tâche, str
             froce, bool
    Effet : log (time.perf_counter()-tic) pour la tâche précisée
            Si force est faux, ne log que pour un temps>.1s
    Sortie : instant où a été lancé cette fonction. 
    """
    tac = time.perf_counter()
    temps = tac-tic
    if temps>.1 or force:
        LOG(f"{round(time.perf_counter()-tic, 2)}s pour {tâche}", "perfs", bavard=bavard)
    return tac


# Une fabrique de décorateurs.
def mesure_temps(nom, temps, nb_appels):
    """
    Entrées : temps et nb_appels deux dicos dont nom est une clef.
    """
    def décorateur(f):
        def nv_f(*args, **kwargs):
            tic=time.perf_counter()
            res=f(*args, **kwargs)
            temps[nom]+=time.perf_counter()
            nb_appels[nom]+=1
            return res
        return nv_f
    return décorateur
        
