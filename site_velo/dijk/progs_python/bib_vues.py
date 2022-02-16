# -*- coding:utf-8 -*-

import re


def bool_of_checkbox(dico, clef):
    """
    Entrée : dico issu d’un POST
             clef
    Renvoie True si la clef est présente dans le dico et la valeur associée est  'on'
    """
    return clef in dico and dico[clef]=="on"

    
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

