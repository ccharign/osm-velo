# -*- coding:utf-8 -*-
import module_graphe
from lecture_adresse.normalisation import VILLE_DÉFAUT, normalise_adresse, normalise_rue, normalise_ville
import re
from récup_données import coords_lieu, coords_of_adresse, cherche_lieu, nœuds_sur_tronçon_local
from petites_fonctions import distance_euc
from params import LOG_PB


class PasTrouvé(Exception):
    pass



def nœuds_of_étape(c, g, bavard=0):
    """ c : chaîne de caractères décrivant une étape. Optionnellement un numéro devant le nom de la rue, ou une ville entre parenthèses.
        g : graphe.
        Sortie : liste de nœuds de g associé à cette adresse.
           Si un numéro est indiqué, renvoie le singleton du nœud de la rue le plus proche.
           Sinon renvoie la liste des nœuds de la rue."""

    c = normalise_adresse(c)
    assert c != ""
    
    if c in g.nœud_of_rue:  # Recherche dans le cache
        if bavard > 1 : print(f"Adresse dans le cache : {c}")
        return g.nœud_of_rue[c]
    else:
        if bavard > 0 :print(f"Pas dans le cache : {c}")
    
    def renvoie(res):
        assert res != []
        assert all(isinstance(s, int) and s in g.digraphe.nodes for s in res)
        g.nœud_of_rue[c] = res
        print(f"Mis en cache : {res} pour {c}")
        return res

    
    ## Analyse de l’adresse. On récupère les variables num, rue, ville
    e = re.compile("(^[0-9]*)([^()]+)(\((.*)\))?")
    essai = re.findall(e, c)
    if bavard > 1: print(f"Résultat de la regexp : {essai}")
    if len(essai) == 1:
        num, rue, _, ville = essai[0]
    elif len(essai) == 0:
        raise SyntaxError(f"adresse mal formée : {c}")
    else:
        print(f"Avertissement : plusieurs interprétations de {c} : {essai}.")
        num, rue, _, ville = essai[0]
    rue = normalise_rue(rue)
    
    #if ville == "": ville = VILLE_DÉFAUT
    ville = normalise_ville(ville.strip())
    if bavard>0: print(f"analyse de l’adresse : num={num}, rue={rue}, ville={ville.avec_code()}")
    
    
    if num == "":
    ## Pas de numéro de rue -> liste de tous les nœuds de la rue
        if bavard > 0 : print("Pas de numéro de rue, je vais renvoyer une liste de nœuds")
        if rue == "":
            raise SyntaxError(f"adresse mal formée : {c}")
        else:
            res = tous_les_nœuds(g, rue, ville=ville, pays="France", bavard=bavard-1)
            #coords = coords_lieu(f"{rue}", ville=ville, bavard=bavard-1)
            #print(f"Je vais prendre le nœud le plus proche de {coords}.")
            #n = g.nœud_le_plus_proche(coords)
            return renvoie(res)

            
    else:
        ## Numéro de rue -> renvoyer un singleton
        num = int(num)
        if bavard > 0 : print("Numéro de rue présent : je vais renvoyer un seul nœud")

        
        return renvoie(un_seul_nœud(g, num, rue, ville=ville, bavard=bavard-1))




def tous_les_nœuds(g, nom_rue, ville=VILLE_DÉFAUT, pays="France", bavard=0):
    """ Entrée : g (graphe)
                 nom_rue (str)
        Sortie : liste des nœuds de cette rue, dans l’ordre topologique si possible.


    Méthode actuelle :
       - essai 1 :  dans g.nœuds[str(ville)][rue]
       - recherche Nominatim pour trouver le nom de la rue dans osm
       - essai 2 : dans g.nœuds avec ce nouveau nom
       - essai 3 : récupérer les nodes osm des way trouvées, et garder ceux qui sont dans g
       - essai 4 : récupérer les nodes de la recherche Nominatim, et garder ceux qui sont dans g
       - essai 5 : coordonnés du premier objet renvoyé par la recherche, et nœud de g le plus proche d’icelui.
    """

    ## Essai 1
    try:
        return g.nœuds[str(ville)][normalise_rue(nom_rue)]
    except KeyError as e :
        print(f"(nœuds_sur_rue) Rue pas en mémoire : {nom_rue} ({ville})  ({e}).")


        ## recherche Nominatim
        lieu = cherche_lieu(nom_rue, ville=ville, pays=pays, bavard=bavard-1)
        if bavard > 0 : print(f"La recherche Nominatim a donné {lieu}.")
        
        nœuds_osm = [] #Ne servira que si on ne trouve pas de way dans lieu
        way_osm = []
        for tronçon in lieu:
            if tronçon.raw["osm_type"] == "way":
                way_osm.append(tronçon.raw)
            elif tronçon.raw["osm_type"] == "node":
                nœuds_osm.append( tronçon.raw )

        ## Recherche dans les ways trouvées
        if len(way_osm)>0:
            tronçon = way_osm[0] # Je récupère le nom à partir du premier rés, a priori le plus fiable...
            nom = tronçon["display_name"].split(",")[0]  # est-ce bien fiable ?
            if bavard >0: print(f"nom trouvé : {nom}")

            ## Essai 2, avec le nom de la rue qu’on vient de récupérer
            if normalise_rue(nom) in g.nœuds[str(ville)] :
                return g.nœuds[str(ville)][normalise_rue(nom)]
            else:
                if bavard >0: print(f"(nœuds_sur_rue) Rue pas en mémoire : {normalise_rue(nom)} ({ville}).")

                ## Essai 3, prendre les nœuds dans le fichier .osm
                nœuds=[]
                for tronçon in way_osm:
                    id_rue = tronçon["osm_id"]
                    nœuds.extend(nœuds_sur_tronçon_local(id_rue)) # Pourrait être géré par overpass
                if bavard >0: print(f"Dans mon fichier osm local, j’ai trouvé les nœuds suivants : {nœuds}")
                nœuds_de_g = [n for n in nœuds if n in g]
                if bavard >0: print(f"Parmi ces nœuds, voici ceux qui sont dans g : {nœuds_de_g}.")
                if len(nœuds_de_g) > 0:
                    return nœuds_de_g
                #else:
                   
                
                    ## Essai inutile ?
                   # for n in nœuds:
                     #   if n in g:
                      #      return nœuds_rue_of_nom_et_nœud(g.digraphe, n, nom)
                        


        ## Essai 4, avec les nodes trouvés
        if nœuds_osm != []:
            nœuds_de_g = [ n["osm_id"] for n in nœuds_osm if n["osm_id"] in g]
            if nœuds_de_g != []:
                return nœuds_de_g

            
        ## Essai 5 : en se basant sur les coords enregistrées dans osm pour le premier way trouvé.
        if len(lieu)>0:
            truc = lieu[0].raw
            if bavard>0: print(f"Je vais chercher le nœud de g le plus proche de {truc}.")
            return [g.nœud_le_plus_proche( (float(truc["lon"]), float(truc["lat"])), recherche=f"Depuis tous_les_nœuds pour {nom_rue} ({ville})" )]

    
        raise PasTrouvé(f"Pas réussi à trouver de nœud pour {nom_rue} ({ville}).")


    
def filtre_nœuds(nœuds, g):
    """ 
    Entrées : liste de nœuds récupérés par cherche_lieu. Chacun doit être un dictionnaire avec pour clefs au moins "osm_id", "lon", "lat".
    Renvoie les éléments de nœuds qui sont dans g ; si aucun renvoie le nœud de g le plus proche de nœuds[0].
    """
    nœuds_de_g = [ n["osm_id"] for n in nœuds_osm if n["osm_id"] in g]
    if nœuds_de_g != []:
        return nœuds_de_g
    else:
        n=nœuds[0]
        return [g.nœud_le_plus_proche( (float(n["lon"]), float(n["lat"])), recherche=f"Depuis tous_les_nœuds pour {nom_rue} ({ville})" )]

    

def un_seul_nœud(g, num, rue, ville=VILLE_DÉFAUT, bavard=0):
    """ Renvoie un singleton si on dispose d’assez de données pour localiser le numéro. Sinon renvoie tous les nœuds de la rue."""
    try:
        if bavard > 0: print(f"le lance coords_of_adresse pour {num}, {rue}, {ville.avec_code()}.")
        coords = coords_of_adresse(num, rue, ville=ville)
        return [nœud_sur_rue_le_plus_proche(g, coords, rue, ville=ville)]
    except Exception as e:
        raise e
        LOG_PB(f"Échec dans coords_of_adresse : {e}. Je vais renvoyer tous les nœuds pour {rue} ({ville.avec_code()}).")
        return tous_les_nœuds(g, rue, ville=ville, bavard=bavard)
        

    







def nœuds_rue_of_arête(g, s, t):
    """Entrée : g (digraph)
                s, t : deux sommets adjacents
       Sortie : liste des nœuds de la rue contenant l’arête (s, t). La rue est identifiée par le paramètre "name" dans le graphe."""

    déjàVu = {}  # En cas d’une rue qui boucle.
    nom = g[s][t]["name"]
    
    def nœud_dans_direction(g, s, t, res):
        """ Mêmes entrées, ainsi que res, tableau où mettre le résultat.
        t sera mis dans res et noté déjÀVu, mais pas s.

        Renvoie les nœuds uniquement dans la direction (s,t), càd ceux auxquels on accède via t et non via s."""

        res.append(t)
        déjàVu[t] = True
        voisins = [v for v in g[t] if v not in déjàVu and v!=s and g[t][v].get("name", "") == nom]
        if len(voisins) == 0:
            return res
        elif len(voisins) == 1:
            return nœud_dans_direction(g, t, voisins[0], res)
        else:
            print(f"Trop de voisins pour le nœud {t} dans la rue {nom}.")
            return nœud_dans_direction(g, t, voisins[0], res)
       
    return list(reversed(nœud_dans_direction(g, s, t, []))) + nœud_dans_direction(g, t, s, [])


def nœuds_rue_of_nom_et_nœud(g, n, nom):
    """ Entrée : n (int) un nœud de la rue
                 nom (str) le nom de la rue. Doit être le nom exact utilisé par osm et reporté dans le graphe.
        Sortie : liste des nœuds de la rue, dans l’ordre topologique."""

    for v in g[n]:
        if g[n][v].get("name", "") == nom:
            return nœuds_rue_of_arête(g, n, v)
    raise PasTrouvé(f"Pas trouvé de voisin pour le nœud {n} dans la rue {nom}")




def nœud_sur_rue_le_plus_proche(g, coords, nom_rue, ville=VILLE_DÉFAUT, pays="France", bavard=0):
    """ 
    Entrée : g (graphe)
             nom_rue (str)
             coords ( (float, float) )
    Renvoie le nœud sur la rue nom_rue le plus proche de coords."""

    nœuds = tous_les_nœuds(g, nom_rue, ville=ville, pays=pays, bavard=bavard-1)
    tab = [ (distance_euc(g.coords_of_nœud(n),coords), n) for n in nœuds ]
    _, res = min(tab)
    return res
