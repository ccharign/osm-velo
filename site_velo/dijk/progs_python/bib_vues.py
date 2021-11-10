# -*- coding:utf-8 -*-

import re


def bool_of_checkbox(dico, clef):
    """Transforme la valeur venue d’une checkbox via un POST en un brave booléen."""
    try:
        if dico[clef]=="on":
            return True
        else:
            return False
    except KeyError:
        return False

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
        head = head.split("<head>")[1]
        
        body, suite = suite.split("</body>")
        body = body.split("<body>")[1]

        script = suite.split("<script>")[1].split("</script>")[0]
    return (head), body, script

