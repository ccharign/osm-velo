
# -*- coding:utf-8 -*-
import re
from params import STR_VILLE_DÉFAUT, PAYS_DÉFAUT


def partie_commune(c):
    """ Appliquée à tout : nom de ville, de rue, et adresse complète
    Met en minuscules
    Supprime les tirets
    Enlève les accents sur les e """
    étape1 = c.strip().lower().replace("-", " ")
    étape2 = re.sub("é|è|ê|ë","e", étape1)
    return étape2
    

def normalise_adresse(c):
    """ Utilisé pour normaliser les adresses complètes, pour améliorer le cache.
    Actuellement c’est partie_commune(c)"""
    return partie_commune(c)


def normalise_rue(rue):
    """ 
    après l’étape "partie_commune",
    Supprime les «de », «du », «de la ».
    Si deux espaces consécutives, supprime la deuxième.
    """
    
    étape2 = partie_commune(rue)
    à_supprimer = [" du ", " de la ", " de ", " d'",  "  "] #Mettre "de la " avant "de ". Ne pas oublier les espaces.
    regexp = "|".join(à_supprimer)
    return re.sub(regexp, " ", étape2)


class Ville():
    """
    Attributs :
      - code (int ou None)
      - nom (str)
    """
    
    def __init__(self, texte):
        """
        Entrée : chaîne de car au format "code_postal? nom_ville".
        """
        e = re.compile("([0-9]{5})? ?([^ 0-9].*)")
        code, nom = re.fullmatch(e, texte).groups()
        self.nom = partie_commune(nom)
        if code is None:
            self.code=None
        else:
            self.code = int(code)

    def __str__(self):
        return self.nom

    def avec_code(self):
        return f"{self.code} {self.nom}"


    
class Adresse():
    """
    Attributs
      - num (int)
      - rue (str) : nom de la rue complet
      - rue_norm (str) : nom de rue aprèr normalisation (via normalise_rue)
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
        
        rue_n = normalise_rue(rue)
        ville_n = normalise_ville(ville.strip())
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
        Utilisé en particulier pour la recherche Nominatim non structurée (si échec de la recherche structurée) et pour l’affichage pour vérification à l’utilisateur.
        """
        if self.num is not None:
            déb=f"{num} "
        else:
            déb=""
        if self.rue_osm is not None:
            return f"{déb}{self.rue_osm}, {self.ville}, {self.pays}"
        else:
            return f"{déb}{self.rue}, {self.ville}, {self.pays}"
        

VILLE_DÉFAUT = Ville(STR_VILLE_DÉFAUT)
           
def normalise_ville(ville):
    """
    Actuellement transforme la chaîne de car en un objet de la classe Ville.
    La chaîne vide "" est transformée en VILLE_DÉFAUT (défini dans params.py).
    """
    if ville == "": return Ville(STR_VILLE_DÉFAUT)
    else: return Ville(ville)

