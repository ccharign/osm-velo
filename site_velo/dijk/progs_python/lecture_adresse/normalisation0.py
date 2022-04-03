# -*- coding:utf-8 -*-

### Programmes de normalisation qui n’utilisent pas les modèles (pour éviter les dépendances circulaires) ###

import re
from petites_fonctions import multi_remplace, LOG


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

def découpe_adresse(texte, bavard=0):
    """
    Entrée : texte (str)
    Sortie (str*str*str*str) : num, bis_ter, rue, ville
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
    num, bis_ter, rue_initiale = re.findall("(^[0-9]*) *(bis|ter)? *(.*)", num_rue)[0]

    LOG(f"(découpe_adresse) Analyse de l’adresse : num={num}, bis_ter={bis_ter}, rue_initiale={rue_initiale}, ville={ville_t}", bavard=bavard)
    return num, bis_ter, rue_initiale, ville_t


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

