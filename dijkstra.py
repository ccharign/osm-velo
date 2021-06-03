# -*- coding:utf-8 -*-


from heapq import heappush, heappop # pour faire du type List une structure de tas-min

class PasDeChemin(Exception):
    pass


def chemin(g, départ, arrivée, p_détour):
    """  Nécessite une classe graphe avec méthode « voisins » qui prend un sommet s et le pourcentage de détour p_détour et renvoie un itérable de (point, longueur de l'arrête corrigée)"""
    assert p_détour <10, f"J'ai reçu p_détour = {p_détour}. As-tu pensé à diviser par 100 le pourcentage ?"
    dist = {départ: 0.} #dist[s] contient l'estimation actuelle de d(départ, i) si s est gris, et la vraie valeur si s est noir.
    pred = {départ: -1}
    àVisiter =[(0, départ)] # tas des sommets à visiter. Doublons autorisés.

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
        return chemin
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


########## En prenant pour étapes des *ensembles* de sommets ##########

def vers_une_étape(g, départ, arrivée, p_détour, dist, pred):
    """
    Entrées : g, graphe avec méthode voisins qui prend un sommet et un p_détour et qui renvoie une liste de (voisin, longueur de l’arête)
              départ et arrivée, ensembles de sommets
              p_détour ∈ [0,1]
              dist : dictionnaire donnant la distance initiale à prendre pour chaque élément de départ (utile quand départ sera juste une étape intermédiaire)
              pred : dictionnaire des prédécesseurs déjà calculés.

    Effet : pred et dist sont remplis de manière à fournir tous les plus courts chemins d’un sommet de départ vers un sommet d’arrivée, en prenant compte des bonus/malus liés aux valeurs initiales de dist.
    """

    
    àVisiter = []
    for (s, d) in dist.items():
        heappush(àVisiter, (d, s))

    fini = False
    sommetsFinalsTraités = {}
    
    while len(àVisiter) > 0 and not fini:
        
        _, s = heappop(àVisiter)
        
        if s in arrivée:
            sommetsFinalsTraités.add(s)
            fini = len(sommetsFinalsTraités) == len(arrivée)
            
        for t, l in g.voisins(s, p_détour):
                if t not in dist or dist[s]+l < dist[t]:  # passer par s vaut le coup
                    dist[t] = dist[s]+l
                    heappush(àVisiter, (dist[t], t))
                    pred[t] = s

  
def chemin_étapes_ensembles(g, étapes, p_détour):
    """
    Entrées : départ et arrivée, deux sommets
              étapes, une liste d’ensembles de sommets
    Sortie : plus court chemin d’un sommet de étapes[0] vers un sommet de étapes[-1] qui passe par au moins un sommet de chaque étape intéremédiaire.
    """

    dist = {s: 0. for s in étapes[0]}
    pred = {s: -1 for s in étapes[0]}

    for i in range(1, len(étapes)):
        vers_une_étape(g, étapes[i-1], étapes[i], p_détour, dist, pred)
        dist = {s: d for (s, d) in dist.items if s in étapes[i]}  # On efface tout sauf les sommet de l’étape qu’on vient d’atteindre

    try:
        _, sommet_darrivée = min( (dist[s],s) for s in étapes[-1] )  # Sommet d’arrivée le plus proche d’un sommet de départ.
    except KeyError as e:
        raise PasDeChemin(f"Pas de chemin trouvé de {étapes[0]} à {étapes[-1]}")
