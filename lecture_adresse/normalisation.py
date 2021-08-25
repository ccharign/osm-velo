
# -*- coding:utf-8 -*-
import re
from params import STR_VILLE_DÉFAUT

def normalise_adresse(c):
    """ Utilisé pour normaliser les adresse, pour améliorer le cache.
    Actuellement met en minuscule."""
    return c.strip().lower()


def normalise_rue(rue):
    """ 
    Met en minuscules
    Supprime les tirets
    Enlève les accents sur les e
    Supprime les «de », «du », «de la ».
    Si deux espaces consécutives, supprime la deuxième.
    """
    
    étape1 = rue.lower().replace("-", " ")
    étape2 = re.sub("é|è|ê|ë","e", étape1)
    à_supprimer = [" du ", " de la ", " de ", "  "] #Mettre "de la " avant "de ". Ne pas oublier les espaces.
    regexp = "|".join(à_supprimer)
    return re.sub(regexp, " ", étape2)


class Ville():
    """
    Attributs :
      - code (int ou None)
      - nom (str)
    """
    
    def __init__(self, texte):
        e = re.compile("([0-9]{5})? ?([^ 0-9].*)")
        code, nom = re.fullmatch(e, texte).groups()
        self.nom = nom
        if code is None:
            self.code=None
        else:
            self.code = int(code)

    def __str__(self):
        return self.nom

    def avec_code(self):
        return f"{self.code} {self.nom}"



            
def normalise_ville(ville):
    """
    Actuellement transforme la chaîne de car en un objet de la classe Ville.
    La chaîne vide "" est transformée en VILLE_DÉFAUT (défini dans params.py).
    """
    if ville == "": return Ville(STR_VILLE_DÉFAUT)
    else: return Ville(ville)

VILLE_DÉFAUT = Ville(STR_VILLE_DÉFAUT)
