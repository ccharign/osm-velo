# -*- coding:utf-8 -*-
#from module_graphe import Graphe
from recup_donnees import coords_lieu
import dijkstra
from params import LOG_PB


ETA = 0.1

def liste_arêtes(liste_nœuds):
    """ Entrée un chemin par liste de nœuds.
        Sortie : itérateur sur les arêtes. """
    for i in range(len(liste_nœuds)-1):
        yield liste_nœuds[i], liste_nœuds[i+1]

def dico_arêtes(iti):
    """
    Entrée : iti (int list)
    Sortie : ensemble de ses arêtes.
    """
    res=set()
    for a in liste_arêtes(iti):
        res.add(a)
    return res


def lecture_meilleur_chemin(g, chemin, bavard=0):
    """ 
    Entrée : le chemin à suivre, instance de Chemin.
    Effet : Compare chemin avec le chemin renvoyé par g.chemin. Augmente de ETA la cyclabilité de chaque arrête présente dans chemin mais pas dans l'autre et diminue de ETA chaque arrête présente dans l'autre et pas dans chemin.
    Sortie : nb d'arêtes modifiées, longueur du trajet direct

    """
    
    #vieux_chemin = g.chemin_étapes_ensembles(chemin.direct())
    chemin_complet, _ = g.chemin_étapes_ensembles(chemin)
    # Pour vieux chemin, je prends le chemin qui utilise le même nœud de départ et d’arrivée que chemin_complet (pour éviter de biaiser l’apprentissage dans le cas de gros ensemble)
    départ = chemin_complet[0]
    arrivée = chemin_complet[-1]
    vieux_chemin, longueur = dijkstra.chemin(g, départ, arrivée, chemin.p_détour)
    arêtes_chemin = dico_arêtes(chemin_complet)
    arêtes_vieux_chemin = dico_arêtes(vieux_chemin)
    n_modif = 0
    
    # Lecture du nouveau chemin pour augmenter les coeff.
    for a in liste_arêtes(chemin_complet):
        if a not in arêtes_vieux_chemin:
            if bavard >0: print(f"j'augmente la cyclabilité de l'arête {a}")
            n_modif+=1
            g.incr_cyclabilité(a, chemin.p_détour, ETA)

    #Lecture du vieux chemin pour diminuer les coeffs :
    for a in liste_arêtes(vieux_chemin):
        if not a in arêtes_chemin:
            if bavard >0: print(f"je diminue la cyclabilité de l'arête {a}")
            n_modif += 1
            g.incr_cyclabilité(a, chemin.p_détour, -ETA)
            
    if bavard >= 0: print(f"nombre d'arêtes modifiées : {n_modif}")
    return n_modif, longueur


def lecture_plusieurs_chemins(g, chemins, bavard=0):
    """
    Entrées : g (graphe)
              chemins (Chemin list)
    Sortie : nb total d'arêtes modifiées, liste des proportions de modif des chemins.
    (proportion de modif = nb_modif/longueur, pour détecter d'éventuels chemins aberrants)
    """
    n_modif_total = 0
    prop_modif=[]
    for chemin in chemins:
        n_modif, l = lecture_meilleur_chemin(g, chemin, bavard=bavard-1)
        n_modif_total+=n_modif
        prop_modif.append(n_modif/l)
        if chemin.AR:
            n_modif, l == lecture_meilleur_chemin(g, chemin.renversé(), bavard=bavard-1)
            n_modif_total+=n_modif
            prop_modif.append(n_modif/l)
    return n_modif, prop_modif


def n_lectures(n, g, chemins, bavard=0):
    return lecture_jusqu_à_perfection(g, chemins, n_max=n, bavard=bavard)


def lecture_jusqu_à_perfection(g, chemins, n_max=50, bavard=0):
    """ 
    Modifie la cyclabilité jusqu'à ce que le chemin trouvé soit le bon pour tous ceux passés dans la liste chemins.
    n_max : nb max d’itérations
    """
    n_étapes = 0
    n_modif=1
    print("Début de l’apprentissage")
    while n_modif>0 and n_étapes<n_max:  # La fonction lecture_plusieurs_chemins renvoie le nb d'arêtes modifiées.
        n_étapes += 1
        n_modif, prop_modif = lecture_plusieurs_chemins(g, chemins, bavard=bavard) > 0
        if bavard >0:
            print(f" ----- Étape {n_étapes}, {n_modif} arêtes modifiées -----")
    print(f"Entraînement fini en {n_étapes} étapes.")
    if n_étapes==n_max:
        LOG_PB(f"Nombre max d’itérations ({n_max}) atteint lors de l’apprentissage pour les chemins {chemins}.")
