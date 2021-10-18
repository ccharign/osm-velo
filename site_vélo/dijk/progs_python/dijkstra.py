#! usr/bin/python3
# -*- coding:utf-8 -*-

from petites_fonctions import deuxConséc
from heapq import heappush, heappop  # pour faire du type List une structure de tas-min
import copy

class PasDeChemin(Exception):
    pass

## Pour passer à A* il faut connaître la cycla max.



## Pour A* : heuristique qui ne surestime jamais la vraie distance. -> prendre le min {d(s, a)/g.cycla_max pour a dans arrivée}

def heuristique(g, s, arrivée):
    return min(g.d_euc(s,a) for a in arrivée)/g.cycla_max



##############################################################################
############################## Dijkstra de base ##############################
##############################################################################


def chemin(g, départ, arrivée, p_détour):
    """  Nécessite une classe graphe avec méthode « voisins » qui prend un sommet s et le pourcentage de détour p_détour et renvoie un itérable de (point, longueur de l'arrête corrigée)"""
    assert p_détour < 10, f"J'ai reçu p_détour = {p_détour}. As-tu pensé à diviser par 100 le pourcentage ?"
    dist = {départ: 0.}  #dist[s] contient l'estimation actuelle de d(départ, i) si s est gris, et la vraie valeur si s est noir.
    pred = {départ: -1}
    àVisiter =[(0, départ)]  # tas des sommets à visiter. Doublons autorisés.

    fini = False
    while len(àVisiter) > 0 and not fini:
        _, s = heappop(àVisiter)  # dist[s] == d(départ,s) d'après la démo du cours.
        if s == arrivée: fini = True
        else:
            for t, l in g.voisins(s, p_détour):
                if t not in dist or dist[s]+l < dist[t]:  # passer par s vaut le coup
                    dist[t] = dist[s]+l
                    heappush(àVisiter, (dist[t], t))
                    pred[t] = s
                    
    
    ## reconstruction du chemin
    if arrivée in dist:
        chemin = [arrivée]
        s = arrivée
        while s != départ:
            s = pred[s]
            chemin.append(s)
        chemin.reverse()
        return chemin, dist[arrivée]
    else:
        raise PasDeChemin(f"Pas de chemin trouvé de {départ} à {arrivée}")

    

def chemin_étapes(g, c):
    """ Entrée : g : graphe
                 c : objet de la classe chemin
        Sortie : chemin passant par ces points
    """
    s = c.départ()
    res = []
    for t in c.étapes[1:]:
        res.extend(chemin(g, s, t, c.p_détour)[:-1])
        s = t
    res.append(s)
    return res




#######################################################################
########## En prenant pour étapes des *ensembles* de sommets ##########
#######################################################################


def arêtesDoubles(g, s, p_détour):
    """ Itérateur sur les chemins de longueur 2 issus de s"""
    for v1, d1 in g.voisins(s, p_détour):
        for v2, d2 in g.voisins(v1, p_détour):
            if v2!=s:
                yield ((v1,d1), (v2,d2))



def vers_une_étape(g, départ, arrivée, p_détour, dist, pred, première_étape):
    """
    Entrées : g, graphe avec méthode voisins qui prend un sommet et un p_détour et qui renvoie une liste de (voisin, longueur de l’arête)
              départ et arrivée, ensembles de sommets
              p_détour ∈ [0,1]
              dist : dictionnaire donnant la distance initiale à prendre pour chaque élément de départ (utile quand départ sera une étape intermédiaire)
              pred : dictionnaire des prédécesseurs déjà calculés.
              première_étape (bool) : indique si on en est à la première étape du trajet final.

    Effet : pred et dist sont remplis de manière à fournir tous les plus courts chemins d’un sommet de départ vers un sommet d’arrivée, en prenant compte des bonus/malus liés aux valeurs initiales de dist.
    Sauf si première_étape, on impose de passer par au moins une arête de départ.

    Attention : pred pourra contenir des couples par moments !
    """

    àVisiter = []
    for (s, d) in dist.items():
        heappush(àVisiter, (d, s))

    fini = False
    sommetsFinalsTraités = set({})

    def boucle_par_arêtes_doubles(s):
        for ((v1,d1), (v2, d2)) in arêtesDoubles(g, s, p_détour):
             if v1 in départ and (v2 not in dist or dist[s]+d1+d2 < dist[v2]):  # Passer par v1,v2 vaut le coup
                 dist[v2] = dist[s]+d1+d2
                 pred[v2] = (v1,s)
                 heappush(àVisiter, (dist[v2]+heuristique(g, v2, arrivée), v2))

    def boucle_simple(s):
        for t, l in g.voisins(s, p_détour):
                if t not in dist or dist[s]+l < dist[t]:  # passer par s vaut le coup
                    dist[t] = dist[s]+l
                    heappush(àVisiter, (dist[t]+heuristique(g, t, arrivée) , t))
                    pred[t] = s

    
    while len(àVisiter) > 0 and not fini:
        _, s = heappop(àVisiter)
        
        if s in arrivée:
            sommetsFinalsTraités.add(s)
            fini = len(sommetsFinalsTraités) == len(arrivée)
            
        if s in départ and not première_étape and len(départ)>1:
            boucle_par_arêtes_doubles(s)
        else:
            boucle_simple(s)
    if not fini:
        raise PasDeChemin(f"Pas réussi à atteindre l’étape {arrivée}")


                    
def reconstruction(chemin, pred, départ):
    """ Entrées : chemin, la fin du chemin retourné. chemin[0] est le point d’arrivée final, chemin[-1] est un sommet dans l’arrivée de cette étape.
                  départ, sommets de départ de l’étape (structure permettant un «in»)
                  arrivée, sommets d’arrivée de l’étape. Doit être itérable
                  pred, le dictionnaire sommet -> sommet ou couple de sommets précédents, créé par Dijkstra.
        Effet : remplit chemin avec un plus court trajet de chemin[-1] vers un sommet de départ.
    """  
    s = chemin[-1]
    while s not in départ:
        if isinstance(pred[s], int):
            s = pred[s]
            chemin.append(s)
        else:
            sp, spp = pred[s]
            chemin.extend((sp,spp))
            s=spp


def chemin_étapes_ensembles(g, c, bavard=0):
    """
    Entrées : départ et arrivée, deux sommets
              c, instance de Chemin (c.étapes est une liste d’Étapes. Pour toute étape é, é.nœuds est une liste de nœuds.)
    Sortie : plus court chemin d’un sommet de étapes[0] vers un sommet de étapes[-1] qui passe par au moins une arête de chaque étape intéremédiaire.
    """
    
    étapes = c.étapes
    départ = étapes[0].nœuds
    arrivée = étapes[-1].nœuds
    
    dist = {s: 0. for s in départ}
    pred = {s: -1 for s in départ}
    preds_précs = []

    for i in range(1, len(étapes)):
        if bavard>0:
            print(f"Recherche d’un chemin de {étapes[i-1]} à {étapes[i]}.")
        vers_une_étape(g, étapes[i-1].nœuds, étapes[i].nœuds, c.p_détour, dist, pred, i==1)
        if bavard>0: print(f"Je suis arrivé à {étapes[i]}")
        preds_précs.append(copy.deepcopy(pred))  # pour la reconstruction finale
        # preds_précs[k] contient les données pour aller de étapes[k] vers étapes[k+1], k==i-1
        dist = {s: d for (s, d) in dist.items() if s in étapes[i].nœuds}  # On efface tout sauf les sommets de l’étape qu’on vient d’atteindre

    if all(s not in dist for s in arrivée):
        raise PasDeChemin(f"Pas de chemin trouvé pour {c}.")
    else:
        _, fin = min(((dist[s], s) for s in arrivée if s in dist))
        chemin = [fin]
        for i in range(len(étapes)-1, 0, -1):
            reconstruction(chemin, preds_précs[i-1], étapes[i-1].nœuds)
        chemin.reverse()
        return chemin, dist[fin]

