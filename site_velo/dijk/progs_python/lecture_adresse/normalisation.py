
# -*- coding:utf-8 -*-
import re
from params import PAYS_DÉFAUT, CHEMIN_NŒUDS_RUES, LOG_PB, TOUTES_LES_VILLES, LOG, DONNÉES
from dijk.models import Rue, CacheNomRue
from lecture_adresse.arbresLex import ArbreLex # Arbres lexicographiques et distance d’édition
import time
from petites_fonctions import chrono
import os
from recup_donnees import cherche_lieu
from .normalisation0 import partie_commune, normalise_adresse, prétraitement_rue


class AdresseMalFormée(Exception):
    pass


### Villes ###

#tic=time.perf_counter()
#print("Création du dico et de l’arbre lex de toutes villes.")
# ARBRE_VILLES=ArbreLex()
# for nom in TOUTES_LES_VILLES.keys():
#     ARBRE_VILLES.insère(nom)
#chrono(tic, "Arbre lex des villes")
# ---> maintenant attribut de Graphe_django
    
class Ville():
    """
    Attributs :
      - code (int ou None)
      - nom_norm (str) : nom, normalisé par la fonction partie_commune
      - nom_complet (str) : le nom pas encore normalisé
    """
    
    def __init__(self, g, texte, tol=2):
        """
        Entrée : chaîne de car au format "(code_postal)? nom_ville". Par exemple  ’64000 Pau’ ou ’Bizanos’.
        """

        # Découpage de la chaîne
        e = re.compile("([0-9]{5})? *([^ 0-9].*)")
        res = re.fullmatch(e, texte.strip())
        if res:
            code, nom = res.groups()
        else:
            raise RuntimeError(f"nom de ville mal formé : {texte}")
        

        # Récupération du nom de la ville dans l’arbre
        v_d = g.ville_la_plus_proche(nom, tol=tol)
        nom_corrigé = v_d.nom_complet
        code_corrigé = v_d.code
        if code and int(code)!= code_corrigé:
            LOG_PB(f"Avertissement : j’ai corrigé le code postal de {code} à {code_corrigé} pour la ville {nom_corrigé}. Chaîne initiale {texte}")
            
        # Enregistrement des données
        self.nom_complet = nom_corrigé
        self.nom_norm = partie_commune(nom_corrigé)
        self.code = code_corrigé

    def __str__(self):
        """ Renvoie le nom non normalisé."""
        return self.nom_complet

    def avec_code(self):
        if self.code is not None:
            c=str(self.code) + " "
        else:
            c=""
        return f"{c}{self}"


    
#VILLE_DÉFAUT = Ville(STR_VILLE_DÉFAUT)
# ---> dans g.ville_défaut



def normalise_ville(g, z_d, ville):
    """
    Actuellement transforme la chaîne de car en un objet de la classe Ville.
    La chaîne vide "" est transformée en g.ville_défaut.
    """
    if ville == "":
        return Ville(g, z_d.ville_défaut.nom_complet)
    else:
        return Ville(g, ville)


    
### Rue ###
    


def créationArbre():
    """ 
    Lit le csv CHEMIN_NŒUDS_RUES, en extrait les noms de toutes les rues. Enregistre pour chaque ville l’arbre lexicographique de ses rues dans un fihier portant le nom de la ville, normalisé via str(normalise_ville(...)).
    rema : dans le csv, les noms des rues et des villes sont supposées avoir l’orthographe d’osm.
    """
    res = {}
    print(f"Chargement de l’arbre des rues depuis {CHEMIN_NŒUDS_RUES}.")
    with open(CHEMIN_NŒUDS_RUES, "r", encoding="utf-8") as entrée:
        for ligne in entrée:
            ville, rue, _ = ligne.strip().split(";")
            ville_n = str(normalise_ville(ville))
            if ville_n not in res: res[ville_n] = ArbreLex()
            res[ville_n].insère(prétraitement_rue(rue))

    for ville_n, arbre in res.items():
        arbre.sauv(os.path.join(DONNÉES, ville_n))
    return res


def arbre_rue_dune_ville(ville_d, rues):
    """
    Entrée : ville_d (mo.Ville)
             rues (str iterable), rues déjà normalisées
    Effet: crée le fichier contenant l'arbre des rue de la ville. Le fichier porte le nom ville_d.nom_norm
    """
    res = ArbreLex()
    for rue in rues:
        res.insère(rue)
    res.sauv(os.path.join(DONNÉES, ville_d.nom_norm))

#créationArbre()

# def charge_arbres_rues(g):
#     """
#     Renvoie le dictionnaire ville (normalisée) -> arbre de ses rues
#     """
#     res={}
#     for ville in TOUTES_LES_VILLES.keys():
#         ville_n = str(normalise_ville(g, ville))
#         res[ville_n] = ArbreLex.of_fichier(os.path.join(DONNÉES, ville_n))
#     return res

# tic=time.perf_counter()
# ARBRE_DES_RUES = charge_arbres_rues()
# chrono(tic, "Arbre lex des rues")

# ---> dans g.arbres_des_rues

def dans_cache_nom_rue(nom, z_d):
    """
    Entrée :
      nom (str), nom passé par la fonction prétraitement_rue
      z_d (Zone)
    Sortie (str ou None) : nom_osm associé à nom dans CacheNomRue s’il y en a un.
    """
    essai = CacheNomRue.objects.filter(nom=nom, zone=z_d)
    if essai: return essai.first().nom_osm


def normalise_rue(g, z_d, rue, ville, persevérant=True, rés_nominatim=None, nv_cache=1, tol=2, bavard=0):
    """
    Entrées : 
      - z_d (Zone)
      - ville (instance de Ville)
      - rue (str)
      - rés_nominatim : résultat d’une éventuelle recherche nominatim précédente.

    Sortie: ( nom normalisé de la rue, nom complet de la rue, rés de la recherche Nominatim ou None).

    Params:
        persevérant : si True, lance une recherche Nominatim en cas d’échec de la recherche dans g.arbres_des_rues.
        nv_cache : (À FAIRE) si >=2, mets en cache une association nom rentré -> nom osm si le nom entré n’était pas une rue reconnue.
    
    Fonction finale de normalisation d’un nom de rue. Applique prétraitement_rue puis recherche s’il y a un nom connu à une distance d’édition inférieure à tol (càd à au plus tol fautes de frappe de rue) dans l’arbre lex g.arbres_des_rues[ville.nom_norm], auquel cas c’est ce nom qui sera renvoyé.
    """

    étape1 = prétraitement_rue(rue)
    
    res, d =  g.arbres_des_rues[ville.nom_norm].mots_les_plus_proches(étape1, d_max=tol)
    if len(res)==1:
        LOG(f"Nom trouvé à distance {d} de {rue} : {list(res)[0]}", bavard=bavard-1)
        rue_n = list(res)[0]
        # Récupérons le nom complet dans la base
        r=Rue.objects.get(nom_norm=rue_n, ville__nom_norm=ville.nom_norm)
        return rue_n, r.nom_complet, None
        
    else:
        LOG(f"(normalise_rue) {étape1} pas dans l’arbre lex des rues de {ville} ({tol} fautes de frappes tolérées).", bavard=bavard)

        # Autre nom dans le cache ?
        essai = dans_cache_nom_rue(étape1, z_d)
        if essai and rue!=essai:
            LOG(f"J’ai trouvé {essai} dans le cache.", bavard=bavard)            
            #return normalise_rue(g, z_d, essai, ville, persevérant=persevérant, bavard=bavard, rés_nominatim=rés_nominatim, nv_cache=0, tol=tol)
            return prétraitement_rue(essai), essai, None
        
        # Résultats ambigüs dans l’arbre
        if len(res)>1:
            # Devrait être très rare
            LOG(f"Rues les plus proches de {rue} : {res}. Je ne sais que choisir, du coup je reste avec {rue} (normalisé en {étape1}).",
                bavard=bavard+1)
            return étape1, rue, rés_nominatim
        
        # Abandon si non persévérant
        elif not persevérant :
            LOG("Je laisse tomber", bavard=bavard+1)
            return étape1, rue, rés_nominatim

        # Recherche d’un autre nom sur nominatim
        else:
            LOG(f"(normalise_rue) Je lance une recherche Nominatim avec '{rue}, {ville}'.", bavard=bavard)
            lieu = cherche_lieu(Adresse(g, z_d, f"{rue}, {ville}", norm_rue=False, bavard=bavard-2 ), bavard=bavard-1)
            LOG(f"(normalise_rue) La recherche Nominatim a donné {lieu}.", bavard=bavard)
            if not lieu:
                LOG_PB(f"Pas de lieu trouvé pour {rue}")
                return étape1, rue, lieu
            
            nom_osm = None
            # Préférence pour les ways
            way_osm = [ t.raw for t in lieu if t.raw["osm_type"]=="way"]
            if len(way_osm)>0:            
                nom_osm = way_osm[0]["display_name"].split(",")[0]  # est-ce bien fiable ?
            else:
                nom_osm = lieu[0].raw["display_name"].split(",")[0]

            if prétraitement_rue(nom_osm)!=étape1:
                LOG("Nouveau nom différent de l’ancien")
                if nv_cache>1:
                    LOG(f"Je mets dans CacheNomRue la valeur {nom_osm} pour le nom prétraité {étape1}")
                    CacheNomRue.ajoute(étape1, nom_osm, z_d)

                LOG(f"(normalise_rue) Nom récupéré : {nom_osm}. Je relance normalise_rue avec celui-ci.", bavard=bavard)
                return normalise_rue(g, z_d, nom_osm, ville, persevérant=False, rés_nominatim=lieu, tol=tol, bavard=bavard)
            else:
                LOG(f"Pas de différence significative entre {rue} et {nom_osm}")
                return étape1, nom_osm, lieu


    
### Adresses ###

    
class Adresse():
    """
    Attributs
      - num (int)
      # supprimé - rue (str) : nom de la rue complet
      - rue_norm (str) : nom de rue après normalisation (via normalise_rue)
      - rue_osm (str) : nom de la rue trouvé dans osm (le cas échéant)
      - rue_initiale (str) : le nom initialement fourni à __init__
      - ville (instance de Ville)
      - pays
      - rés_nominatim : résultat de cherche_lieu s’il y a eu un appel à cette fonction.
    """
    
    def __init__(self, g, z_d, texte, norm_rue=True, nv_cache=1, bavard=0):
        """ 
        Entrée :
            g (graphe)
            z_d (Zone)
            texte d’une adresse. Format : (num)? rue (code_postal? ville)
        """
        
        # Découpage selon les virgules
        trucs = texte.split(",")
        if len(trucs)==1:
            num_rue, ville_t = trucs[0], ""
        elif len(trucs)==2:
            num_rue, ville_t = trucs
        elif len(trucs)==3:
            num_rue, ville_t, pays = trucs
        else:
            raise AdresseMalFormée(f"Trop de virgules dans {texte}.")
        ville_t = ville_t.strip()
        
        # numéro de rue et rue
        num, rue_initiale = re.findall("(^[0-9]*) *(.*)", num_rue)[0]

        LOG(f"(Adresse.__init__) Analyse de l’adresse : num={num}, rue_initiale={rue_initiale}, ville={ville_t}", bavard=bavard)
        
        # Normalisation de la ville et de la rue
        ville_n = normalise_ville(g, z_d, ville_t) # ville_t doit-elle contenir le code postal ?
        rés_nominatim = None
        rue_osm = None
        rue_n = None
        if norm_rue:
            rue_n, rue_osm, rés_nominatim = normalise_rue(g, z_d, rue_initiale, ville_n, nv_cache=nv_cache, bavard=bavard-1)
        # else:
        #     rue = rue_initiale
        #     rue_n = None
        
        LOG(f"(Adresse.__init__) Après normalisation : num={num}, rue_initiale={rue_initiale}, rue_n={rue_n}, rue_osm={rue_osm}, ville_n={ville_n}", bavard=bavard)

        # Initialisation des attributs
        if num=="":
            self.num=None
        else:
            self.num=int(num)
        #self.rue = rue
        self.rue_initiale=rue_initiale
        self.rue_norm = rue_n
        self.rue_osm = rue_osm
        self.ville = ville_n
        self.pays=PAYS_DÉFAUT
        self.rés_nominatim=rés_nominatim

        
    def rue(self):
        """
        Renvoie le nom le plus précis disponible pour la rue.
        """
        if self.rue_osm:
            return self.rue_osm
        else:
            return self.rue_initiale

    def num_ou_pas(self):
        """
        Sortie (str) : self.num+' ' si num présent, '' sinon.
        """
        if self.num:
            return f"{self.num} "
        else:
            return ""
    
    def __str__(self):
        """
        Utilisé en particulier pour l’enregistrement dans chemins.csv, pour l’affichage pour vérification à l’utilisateur, et pour la recherche de coordonnése
        """
        return f"{self.num_ou_pas()}{self.rue()}, {self.ville}"
        
    def pour_nominatim(self):
        """
        Renvoie une chaîne de car pour la recherche Nominatim non structurée (si échec de la recherche structurée).
        """
        return f"{self.num_ou_pas()}{self.rue()}, {self.ville.avec_code()}, {self.pays}"

    
    def pour_cache(self):
        """
        Sortie (str) : chaîne utilisée dans Cache_adresse.
        """
        return f"{self.num_ou_pas()}{self.rue()}, {self.ville}"
