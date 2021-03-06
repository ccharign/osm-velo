# -*- coding:utf-8 -*-

import re

from dijk.progs_python.chemins import Étape, ÉtapeArête

def dict_of_get(g):
    """
    Un simple dict(g) semble ne pas fonctionner...
    """
    return dict(g.items())


def récup_données(dico, cls_form, validation_obligatoire=True):
    """
    Entrée :
        dico, contient le résultat d’un GET ou d’un POST
        cls_form, classe du formulaire correspondant.
    Effet:
        lève une exception si form pas valide
    Sortie:
       dico transformé en un vrai type dict, auquel est rajouté le contenu du form.cleaned_data
    """
    form = cls_form(dico)
    if not form.is_valid():
        if validation_obligatoire:
            raise ValueError(f"Formulaire pas valide : {form}.\n Erreurs : {form.errors}")
        else:
            print(f"Formulaire pas valide : {form}.\n Erreurs : {form.errors}")
    données = dict_of_get(dico)
    données.update(form.cleaned_data)
    return données


def z_é_i_d(g, données):
    """
    Entrée (dico) : résultat d’un GET ou d’un POST d’un formulaire de recherche d’itinéraire.
    Sortie (Zone, Étapes list, Étapes list, float list) : (zone, étapes, étapes_interdites, ps_détours)
    Effet : la zone est chargée si pas déjà le cas.
    """
    
    z_d = g.charge_zone(données["zone"])
    if "partir_de_ma_position" in données and données["partir_de_ma_position"]:
        coords = tuple(map(float, données["localisation"].split(";")))
        assert len(coords) == 2, f"coords n'est pas de longueur 2 {coords}"
        données["départ_coords"] = str(coords)[1:-1]
        d = ÉtapeArête.of_coords(coords, g, z_d)
    else:
        d = Étape.of_dico(données, "départ", g, z_d)


    a = Étape.of_dico(données, "arrivée", g, z_d)
    noms_étapes = [é for é in données["étapes"].strip().split(";") if len(é)>0]
    étapes = [d] + [Étape.of_texte(é, g, z_d) for é in noms_étapes] + [a]
    ps_détour = list(map( lambda x: float(x)/100, données["pourcentage_détour"].split(";")) )
    étapes_interdites = [Étape.of_texte(r, g, z_d) for r in données["rues_interdites"].strip().split(";") if len(r)>0]

    return z_d, étapes, étapes_interdites, ps_détour


def bool_of_checkbox(dico, clef):
    """
    Entrée : dico issu d’un POST
             clef
    Renvoie True si la clef est présente dans le dico et la valeur associée est  'on'
    """
    return clef in dico and dico[clef] == "on"

    
def énumération_texte(l):
    """
    Entrée : liste de str
    Sortie : une str contenant les éléments de l séparés par des virgules, sauf dernier qui est séparé par le mot « et »
    """
    if len(l)==0:
        return ""
    elif len(l)==1:
        return l[0]
    else:
        return ", ".join(l[:-1]) + " et " + l[-1]

    
def sans_style(texte):
    """
    Entrée : du code html (str)
    Sortie : le code sans les lignes entourées de balises <style>...</style>
    """
    
    x=re.findall("(.*?)<style>.*?</style>(.*)", texte) # ? : non greedy
    if x:
        return x[0][0] + sans_style(x[0][1])
    else:
        return texte

    
def récup_head_body_script(chemin):
    """ Entrée : adresse d’un fichier html
        Sortie : la partie body de celui-ci
    """
    with open(chemin) as entrée:
        tout=entrée.read()
        
        head, suite = tout.split("</head>")
        lignes_head = head.split("<head>")[1].split("\n")
        à_garder = []
        for ligne in lignes_head:
            if not ("bootstrap in ligne"):
                à_garder.append(ligne)
        head_final = "\n".join(à_garder)
        
        
        body, suite = suite.split("</body>")
        body = body.split("<body>")[1]

        script = suite.split("<script>")[1].split("</script>")[0]
    return head, body, script

