
# -*- coding:utf-8 -*-
import re
from params import STR_VILLE_DÉFAUT, PAYS_DÉFAUT, CHEMIN_NŒUDS_RUES
from dijk.progs_python.lecture_adresse.arbresLex import ArbreLex # Arbres lexicographiques et distance d’édition




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


class Ville():
    """
    Attributs :
      - code (int ou None)
      - nom (str) : nom, normalisé par la fonction partie_commune
      - nom_initial (str) : le nom pas encore normalisé
    """
    
    def __init__(self, texte):
        """
        Entrée : chaîne de car au format "code_postal? nom_ville".
        """
        e = re.compile("([0-9]{5})? ?([^ 0-9].*)")
        code, nom = re.fullmatch(e, texte.strip()).groups()
        self.nom_initial = nom
        self.nom = partie_commune(nom)
        if code is None:
            self.code=None
        else:
            self.code = int(code)

    def __str__(self):
        return self.nom

    def avec_code(self):
        return f"{self.code} {self.nom}"

VILLE_DÉFAUT = Ville(STR_VILLE_DÉFAUT)
           
def normalise_ville(ville):
    """
    Actuellement transforme la chaîne de car en un objet de la classe Ville.
    La chaîne vide "" est transformée en VILLE_DÉFAUT (défini dans params.py).
    """
    if ville == "": return Ville(STR_VILLE_DÉFAUT)
    else: return Ville(ville)


### Rue ###
    

def prétraitement_rue(rue):
    """ 
    Après l’étape "partie_commune", supprime les «de », «du », «de la ».
    Si deux espaces consécutives, supprime la deuxième.
    """
    
    étape1 = partie_commune(rue)
    à_supprimer = [" du ", " de la ", " de ", " d'",  "  "] # Mettre "de la " avant "de ". Ne pas oublier les espaces.
    regexp = "|".join(à_supprimer)
    return re.sub(regexp, " ", étape1)


def créationArbre():
    """ 
    Lit le csv CHEMIN_NŒUDS_RUES, en extrait les noms de toutes les rues et met le tout dans un dictionnaire ville -> arbre des rues.
    rema : dans le csv, les noms des rues et des villes sont supposées avoir l’orthographe d’osm.
    """
    res = {}
    with open(CHEMIN_NŒUDS_RUES, "r") as entrée:
        for ligne in entrée:
            ville, rue, _ = ligne.strip().split(";")
            ville_n = str(normalise_ville(ville))
            if ville_n not in res: res[ville_n] = ArbreLex()
            res[ville_n].insère(prétraitement_rue(rue))
    return res


ARBRE_DES_RUES = créationArbre()

def normalise_rue(rue, ville, tol=3, bavard=0):
    """
    Entrées : 
      - ville (instance de Ville)
      - rue (str)

    Fonction finale de normalisation d’un nom de rue. Applique partie_commune puis prétraitement_rue puis recherche s’il y a un nom connu à une distance d’édition inférieure à tol (càd à au plus tol fautes de frappe de rue), auquel cas c’est ce nom qui sera renvoyé.
    """
    étape1 = prétraitement_rue(rue)
    res, d=  ARBRE_DES_RUES[ville.nom].mots_les_plus_proches(étape1, d_max=tol)
    if len(res)==1:
        if bavard>0:
            print(f"Nom trouvé à distance {d} de {rue} : {list(res)[0]}")
        return list(res)[0]
    elif len(res)>1:
        # Devrait être très rare
        print(f"Rues les plus proches de {rue} : {res}. Je ne sais que choisir, du coup je reste avec {rue} (normalisé en {étape1}).")
        return étape1
    else:
        # L’adresse fournie n’était sûrement pas un nom de rue.
        print(f"(normalise_rue) Pas de rue connue à moins de {tol} fautes de frappe de {rue} dans la ville {ville}. Je renvoie {étape1}.")
        return étape1
    


    
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
    
    def __init__(self, texte, bavard=0):
        """ 
        Entrée : texte d’une adresse. Format : (num)? rue (code_postale? ville)
        """
        e = re.compile("(^[0-9]*)([^()]+)(\((.*)\))?")
        essai = re.findall(e, texte)
        if bavard > 1: print(f"Résultat de la regexp : {essai}")
        if len(essai) == 1:
            num, rue, _, ville = essai[0]
        elif len(essai) == 0:
            raise SyntaxError(f"adresse mal formée : {texte}")
        else:
            print(f"Avertissement : plusieurs interprétations de {texte} : {essai}.")
            num, rue, _, ville = essai[0]

        if bavard>0: print(f"analyse de l’adresse : num={num}, rue={rue}, ville={ville.avec_code()}")
        
        
        ville_n = normalise_ville(ville)
        rue_n = normalise_rue(rue, ville_n)
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
        Utilisé en particulier pour l’enregistrement dans chemins.csv et pour l’affichage pour vérification à l’utilisateur.
        """
        if self.num is not None:
            déb=f"{self.num} "
        else:
            déb=""
        if self.rue_osm is not None:
            return f"{déb}{self.rue_osm} ({self.ville.avec_code})"
        else:
            return f"{déb}{self.rue}, {self.ville.avec_code}"

        
    def pour_nominatim(self):
        """
        Renvoie une chaîne de car pour la recherche Nominatim non structurée (si échec de la recherche structurée).
        """
        if self.num is not None:
            déb=f"{self.num} "
        else:
            déb=""
        if self.rue_osm is not None:
            return f"{déb}{self.rue_osm}, {self.ville.avec_code}, {self.pays}"
        else:
            return f"{déb}{self.rue}, {self.ville.avec_code}, {self.pays}"


