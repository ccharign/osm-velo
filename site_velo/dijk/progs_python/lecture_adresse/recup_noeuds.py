# -*- coding:utf-8 -*-
#import module_graphe
from lecture_adresse.normalisation import VILLE_DÉFAUT, normalise_adresse, normalise_rue, normalise_ville, Adresse
import re
from recup_donnees import coords_lieu, coords_of_adresse, cherche_lieu, nœuds_sur_tronçon_local, cherche_adresse_complète, rue_of_coords
from petites_fonctions import distance_euc
from params import LOG_PB


### Module pour associer une liste de nœuds à une adresse. ###


class PasTrouvé(Exception):
    pass



def nœuds_of_étape(c, g, bavard=0):
    """ c : chaîne de caractères décrivant une étape. Optionnellement un numéro devant le nom de la rue, ou une ville entre parenthèses.
        g : graphe.
        Sortie : (liste de nœuds de g associé à cette adresse, l’adresse de type Adresse)
           Si un numéro est indiqué, la liste de nœuds est le singleton du nœud de la rue le plus proche.
           Sinon c’est la liste de tous les nœuds connus de la rue.
    """

    # Lecture de l’adresse
    c = normalise_adresse(c)
    assert c != ""
    ad = Adresse(c, bavard=bavard-1)
    
    # Recherche dans le cache
    essai = g.nœuds_of_cache(c)
    if essai is not None:  
        if bavard > 1 : print(f"Adresse dans le cache : {c}")
        return essai, ad
    else:
        if bavard > 0 :print(f"Pas dans le cache : {c}")

    # Fonction de mise en cache
    def renvoie(res):
        assert res != []
        for s in res:
            assert isinstance(s,int)
            if s not in g :
                raise ValueError("Le nœud {s} obtenu pour {c} n’est pas dans le graphe. Liste des nœuds obtenus : {res}.")
        g.met_en_cache(c, res)
        print(f"Mis en cache : {res} pour {c}")
        return res, ad

    
    if ad.num is None:
        ## Pas de numéro de rue -> soit c’est une rue entière, soit c’est un batiment spécial
        ## liste de tous les nœuds de la rue
        if bavard > 0 : print("Pas de numéro de rue, je vais renvoyer une liste de nœuds")
        if ad.rue == "":
            raise SyntaxError(f"adresse mal formée : {c}")
        else:
            res = tous_les_nœuds(g, ad, bavard=bavard-1)
            return renvoie(res)

    else:
        ## Numéro de rue -> renvoyer un singleton
        if bavard > 0 : print("Numéro de rue présent : je vais renvoyer un seul nœud")
        return renvoie(un_seul_nœud(g, ad, bavard=bavard-1))




def tous_les_nœuds(g, adresse, bavard=0):
    """ Entrée : g (graphe)
                 adresse : instance de Adresse
        Sortie : liste des nœuds de cette rue, dans l’ordre topologique si possible.


    Méthode actuelle :
       - essai 1 :  via la méthode g.nœuds_of_rue (en local)
       - recherche Nominatim pour trouver le nom de la rue dans osm
       - essai 2 : dans g.nœuds avec ce nouveau nom
       - (supprimé car lent) essai 3 : récupérer les nodes osm des way trouvées dans le .osm local, et garder ceux qui sont dans g
       - essai 4 : récupérer les nodes de la recherche Nominatim, et garder ceux qui sont dans g
       - essai 5 : coordonnés du premier objet renvoyé par la recherche, et nœud de g le plus proche d’icelui.
    """

    ## Essai 1
    essai1 = g.nœuds_of_rue(adresse.ville.nom_norm, adresse.rue_norm)
    if essai1 is not None:
        return essai1
    else :
        print(f"(nœuds_sur_rue) Rue pas en mémoire : {adresse}.")


        ## recherche Nominatim
        lieu = cherche_lieu(adresse, bavard=bavard-1)
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
            print(f"nom trouvé : {nom}")
            adresse.rue_osm = nom

            ## Essai 2, avec le nom de la rue qu’on vient de récupérer
            nom_n = normalise_rue(nom, adresse.ville)
            essai2 = g.nœuds_of_rue(adresse.ville.nom_norm, nom_n)
            if essai2 is not None :
                return essai2
            else:
                if bavard >0: print(f"(nœuds_sur_rue) Rue pas en mémoire : {adresse}.")

                ## Essai 3, prendre les nœuds dans le fichier .osm
                # nœuds=[]
                # for tronçon in way_osm:
                #     id_rue = tronçon["osm_id"]
                #     nœuds.extend(nœuds_sur_tronçon_local(id_rue)) # Pourrait être géré par overpass
                # LOG_PB(f"Dans mon fichier osm local, j’ai trouvé les nœuds suivants : {nœuds}")
                # print(" J’utilise une méthode inefficace : nœuds_de_g = [n for n in nœuds if n in g] dans recup_noeuds.py.")
                # nœuds_de_g = [n for n in nœuds if n in g]
                # LOG_PB(f"Parmi ces nœuds, voici ceux qui sont dans g : {nœuds_de_g}.")
                # if len(nœuds_de_g) > 0:
                #     return nœuds_de_g
                #else:
                   
                
                    ## Essai inutile ?
                   # for n in nœuds:
                     #   if n in g:
                      #      return nœuds_rue_of_nom_et_nœud(g.digraphe, n, nom)
                        


        ## Essai 4, avec les nodes trouvés
        if nœuds_osm != []:
            nœuds_de_g = [ n["osm_id"] for n in nœuds_osm if n["osm_id"] in g]
            if len(nœuds_de_g) > 0:
                return nœuds_de_g

            
        ## Essai 5 : en se basant sur les coords enregistrées dans osm pour le premier élément renvoyé par Nominatim
        ## Ce devrait la situation notamment pour toutes les recherches qui ne sont pas un nom de rue (bâtiment public, commerce...)
        if len(lieu)>0:
            truc = lieu[0].raw
            adresse.rue_osm = lieu[0].raw["display_name"].split(",")[0]
            print(f"Je vais chercher le nœud de g le plus proche de {truc}.")
            coords = (float(truc["lon"]), float(truc["lat"]))
            rue, ville, code = rue_of_coords(coords)
            if bavard>0:print(f"J’ai obtenu l’adresse suivante : {rue} ({code} {ville}).")
            return [nœud_sur_rue_le_plus_proche(g, coords, Adresse(f"{rue} ({ville})"))]
            #return [g.nœud_le_plus_proche( coords, recherche=f"Depuis tous_les_nœuds pour {adresse}." )]

    
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

    

def un_seul_nœud(g, adresse, bavard=0):
    """ Renvoie un singleton si on dispose d’assez de données pour localiser le numéro. Sinon renvoie tous les nœuds de la rue."""
    try:
        #if bavard > 0: print(f"Je lance coords_of_adresse pour {adresse}.")
        #coords = coords_of_adresse(adresse)
        #return [nœud_sur_rue_le_plus_proche(g, coords, adresse)]
        if bavard>0:print(f"Récupération des coordonnées de {adresse} via adresse.data.gouv.fr")
        coords = cherche_adresse_complète(adresse, bavard=bavard)
        return [nœud_sur_rue_le_plus_proche(g, coords, adresse, bavard=bavard-1)]
    except Exception as e:
        LOG_PB(f"Échec dans cherche_adresse_complète : {e}. Je vais renvoyer tous les nœuds pour {adresse}). J’efface le numéro de l’adresse.")
        adresse.num=None
        return tous_les_nœuds(g, adresse, bavard=bavard)
        

    







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




def nœud_sur_rue_le_plus_proche(g, coords, adresse, bavard=0):
    """ 
    Entrée : g (graphe)
             adresse (instance de Adresse)
             coords ( (float, float) )
    Renvoie le nœud sur la rue nom_rue le plus proche de coords."""

    nœuds = tous_les_nœuds(g, adresse, bavard=bavard-1)
    if bavard>0:print(f"Nœuds récupérés pour la rue de {adresse} : {nœuds}")
    tab = [ (distance_euc(g.coords_of_nœud(n),coords), n) for n in nœuds ]
    if bavard>0:print(f"distances aux nœuds de la rue : {tab}")
    _, res = min(tab)
    return res
