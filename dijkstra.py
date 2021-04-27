# -*- coding:utf-8 -*-


from heapq import heappush, heappop # pour faire du type List une structure de tas-min

class PasDeChemin(Exception):
    pass


def chemin(g, départ, arrivée, p_détour):
    """  Nécessite une classe graphe avec méthode « voisins » qui prend un sommet s et le pourcentage de détou p_détour et renvoie un itérable de (point, longueur de l'arrête corrigée)"""
    assert p_détour <10, f"J'ai reçu p_détour = {p_détour}. As-tu pensé à diviser par 100 le pourcentage ?"
    dist = {départ:0.} #dist[s] contient l'estimation actuelle de d(départ, i) si s est gris, et la vraie valeur si s est noir.
    pred = {départ:-1}
    àVisiter =[(0,départ)] # tas des sommets à visiter. Doublons autorisés.

    fini = False
    while len(àVisiter)>0 and not fini :
        _, s = heappop(àVisiter) # dist[s] == d(départ,s) d'après la démo du cours.
        if s == arrivée : fini=True
        else:
            for t, l in g.voisins(s, p_détour):
                if t not in dist or dist[s]+l < dist[t] : # passer par s vaut le coup
                    dist[t] = dist[s]+l
                    heappush(àVisiter, (dist[t], t))
                    pred[t]=s
                    
    
    # reconstruction du chemin
    if arrivée in dist :
        chemin=[arrivée]
        s=arrivée
        while s != départ:
            s=pred[s]
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
    res=[]
    for t in c.étapes[1:]:
        res.extend( chemin(g, s, t, c.p_détour)[:-1])
        s=t
    res.append(s)
    return res
