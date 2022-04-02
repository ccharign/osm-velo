# -*- coding:utf-8 -*-

### Programmes de normalisation qui n’utilisent pas les modèles (pour éviter les dépendances circulaires) ###

import re
from petites_fonctions import multi_remplace


def partie_commune(c):
    """ Appliquée à tout : nom de ville, de rue, et adresse complète
    Met en minuscules
    Supprime les tirets
    Enlève les accents sur les e et les à"""
    étape1 = c.strip().lower().replace("-", " ")
    étape2 = re.sub("é|è|ê|ë", "e", étape1)
    étape3 = re.sub("à|ä", "a", étape2)
    return étape3
    

def normalise_adresse(c):
    """ Utilisé pour normaliser les adresses complètes, pour améliorer le cache.
    Actuellement c’est partie_commune(c)"""
    return partie_commune(c)


DICO_REMP={
    "avenue":"α",
    "rue":"ρ",
    "boulevard":"β",
    "allée":"λ",
}


def prétraitement_rue(rue):
    """ 
    Après l’étape "partie_commune", supprime les «de », «du », «de la ».
    Si deux espaces consécutives, supprime la deuxième.
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
            
    return multi_remplace(DICO_REMP, res)

