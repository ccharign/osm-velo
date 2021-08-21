# -*- coding:utf-8 -*-
import re

def normalise_adresse(c):
    """ Utilisé pour normaliser les adresse, pour améliorer le cache.
    Actuellement met en minuscule."""
    return c.strip().lower()


def normalise_rue(rue):
    """ Met en minuscules"""
    return rue.lower()


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

    À réfléchir. Mettre le code postal devant ? Récupérer la liste des communes. les codes postales sont-ils dans le .osm ? -> À rajouter dans initialisation au moment de la lecture du .osm.
    """
    return Ville(ville)
