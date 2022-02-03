
# -*- coding:utf-8 -*-
import re
from params import PAYS_DÉFAUT, CHEMIN_NŒUDS_RUES, LOG_PB, TOUTES_LES_VILLES, LOG, DONNÉES
from dijk.models import Rue
from lecture_adresse.arbresLex import ArbreLex # Arbres lexicographiques et distance d’édition
import time
from petites_fonctions import chrono
import os
from recup_donnees import cherche_lieu

def partie_commune(c):
    """ Appliquée à tout : nom de ville, de rue, et adresse complète
    Met en minuscules
    Supprime les tirets
    Enlève les accents sur les e """
    étape1 = c.strip().lower().replace("-", " ")
    étape2 = re.sub("é|è|ê|ë", "e", étape1)
    return étape2
    

def normalise_adresse(c):
    """ Utilisé pour normaliser les adresses complètes, pour améliorer le cache.
    Actuellement c’est partie_commune(c)"""
    return partie_commune(c)


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
    

def prétraitement_rue(rue):
    """ 
    Après l’étape "partie_commune", supprime les «de », «du », «de la ».
    Si deux espaces consécutives, supprime la deuxième.

    À faire : remplacer les «avenue», «rue», «place», etc par des symboles utf8, de sorte que remplacer l’un par l’autre ne compte que pour une faute de frappe dans la distance d’édition.
    """
    
    étape1 = partie_commune(rue)
    # les chaînes suivantes seront remplacées par une espace.
    à_supprimer = [" du ", " de la ", " de l'", " de ", " d'",  "  "] # Mettre "de la " avant "de ". Ne pas oublier les espaces.
    regexp = "|".join(à_supprimer)
    fini = False
    res = étape1
    # Pour les cas comme « rue de du Forbeth »
    while not fini:
        suivant = re.sub(regexp, " ", res)
        if suivant==res:
            fini=True
        else:
            res=suivant
    return res


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
    Entrée : ville_d (Ville)
             rues (str iterable)
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


def normalise_rue(g, z_d, rue, ville, persevérant=True, tol=2, bavard=0):
    """
    Entrées : 
      - z_d (Zone)
      - ville (instance de Ville)
      - rue (str)

    Sortie: ( nom normalisé de la rue, nom complet de la rue).
    Params:
        persevérant : si True, lance une recherche Nominatim en cas d’échec de la recherche dans g.arbres_des_rues.
    
    Fonction finale de normalisation d’un nom de rue. Applique partie_commune puis prétraitement_rue puis recherche s’il y a un nom connu à une distance d’édition inférieure à tol (càd à au plus tol fautes de frappe de rue), auquel cas c’est ce nom qui sera renvoyé.
    """

    étape1 = prétraitement_rue(rue)
    
    res, d =  g.arbres_des_rues[ville.nom_norm].mots_les_plus_proches(étape1, d_max=tol)
    if len(res)==1:
        if bavard>0:
            print(f"Nom trouvé à distance {d} de {rue} : {list(res)[0]}")
        rue_n = list(res)[0]
        if rue_n!=étape1:
            #il y avait une faute de frappe
            #Retrouvons le nom complet initial
            r=Rue.objects.get(nom_norm=rue_n, ville__nom_norm=ville.nom_norm)
            return rue_n, r.nom_complet
        else:
            return rue_n, rue
            
    elif len(res)>1:
        # Devrait être très rare
        print(f"Rues les plus proches de {rue} : {res}. Je ne sais que choisir, du coup je reste avec {rue} (normalisé en {étape1}).")
        return étape1, rue
    
    elif not persevérant :
        LOG("Je laisse tomber", bavard=bavard)
        return étape1, rue
    
    else:
        print(f"(normalise_rue) Pas de rue connue à moins de {tol} fautes de frappe de {rue} dans la ville {ville}. Je lance une recherche Nominatim.")
        lieu = cherche_lieu(Adresse(g, z_d, f"{rue}, {ville}", norm_rue=False, bavard=bavard-2 ), bavard=bavard-1)
        LOG(f"La recherche Nominatim a donné {lieu}.", bavard=bavard)
        way_osm = [ t.raw for t in lieu if t.raw["osm_type"]=="way"]
        if len(way_osm)>0:            
            tronçon = way_osm[0] # Je récupère le nom à partir du premier rés, a priori le plus fiable...
            nom = tronçon["display_name"].split(",")[0]  # est-ce bien fiable ?
            print(f"Nouvel essai avec le nom suivant : {nom}")
            return normalise_rue(g, z_d, nom, ville, persevérant=False, tol=tol, bavard=bavard)
        else:
            LOG("Pas de way dans le résultat de la recherche Nominatim.")
            return étape1, rue
    


    
### Adresses ###

    
class Adresse():
    """
    Attributs
      - num (int)
      - rue (str) : nom de la rue complet
      - rue_norm (str) : nom de rue après normalisation (via normalise_rue)
      - rue_osm (str) : nom de la rue trouvé dans osm (le cas échéant)
      - ville (instance de Ville)
      - pays
    """
    
    def __init__(self, g, z_d, texte, norm_rue=True, bavard=0):
        """ 
        Entrée :
            g (graphe)
            z_d (Zone)
            texte d’une adresse. Format : (num)? rue (code_postal? ville)
        """
        
        # # Lecture de la regexp
        # e = re.compile("(^[0-9]*) *([^()]+)(\((.*)\))?")
        # essai = re.findall(e, texte)
        # if bavard > 1: print(f"Résultat de la regexp : {essai}")
        # if len(essai) == 1:
        #     num, rue, _, ville = essai[0]
        # elif len(essai) == 0:
        #     raise SyntaxError(f"adresse mal formée : {texte}")
        # else:
        #     print(f"Avertissement : plusieurs interprétations de {texte} : {essai}.")
        #     num, rue, _, ville = essai[0]
        #     rue=rue.strip()

        # Découpage selon les virgules
        trucs = texte.split(",")
        if len(trucs)==1:
            num_rue, ville_t = trucs[0], ""
        elif len(trucs)==2:
            num_rue, ville_t = trucs
        elif len(trucs)==3:
            nom_rue, ville_t, pays = trucs
        ville_t = ville_t.strip()
        
        # numéro de rue et rue
        num, rue = re.findall("(^[0-9]*) *(.*)", num_rue)[0]

        if bavard>0: print(f"analyse de l’adresse : num={num}, rue={rue}, ville={ville_t}")
        
        # Normalisation de la ville et de la rue
        ville_n = normalise_ville(g, z_d, ville_t) # ville_t doit-elle contenir le code postal ?
        if norm_rue:
            rue_n, rue = normalise_rue(g, z_d, rue, ville_n)
        else:
            rue_n = rue
        
        if bavard>0: print(f"après normalisation : num={num}, rue_n={rue_n}, ville_n={ville_n}")

        # Initialisation des attributs
        if num=="":
            self.num=None
        else:
            self.num=int(num)
        self.rue=rue
        self.rue_norm = rue_n
        self.rue_osm = None
        self.ville = ville_n
        self.pays=PAYS_DÉFAUT


    def __str__(self):
        """
        Utilisé en particulier pour l’enregistrement dans chemins.csv, pour l’affichage pour vérification à l’utilisateur, et pour la recherche de coordonnése
        """
        if self.num is not None:
            déb=f"{self.num} "
        else:
            déb=""
        if self.rue_osm is not None:
            return f"{déb}{self.rue_osm}, {self.ville.avec_code()}, {self.pays}"
        else:
            return f"{déb}{self.rue}, {self.ville.avec_code()}, {self.pays}"
        
    def pour_nominatim(self):
        """
        Renvoie une chaîne de car pour la recherche Nominatim non structurée (si échec de la recherche structurée).
        """
        if self.num is not None:
            déb=f"{self.num} "
        else:
            déb=""
        if self.rue_osm is not None:
            return f"{déb}{self.rue_osm}, {self.ville.avec_code()}, {self.pays}"
        else:
            return f"{déb}{self.rue}, {self.ville.avec_code()}, {self.pays}"


