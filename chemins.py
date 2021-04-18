# -*- coding:utf-8 -*-

from récup_données import *
from copy import deepcopy

import module_graphe

#Pour test
#import init_graphe
#g = init_graphe.charge_graphe(bavard=1)


def sans_guillemets(c):
    if c[0]=='"':
        assert c[-1]=='"', f"Guillemets pas comme prévu, dans la chaîne {c}"
        return c[1:-1]
    else:
        return c

class Chemin():
    """ Attributs : - p_détour (float)
                    - étapes (int List), liste de nœuds
                    - AR (bool), indique si le retour est valable aussi.
    """
    def __init__(self, étapes, p_détour, AR):
        self.étapes = étapes
        self.p_détour = p_détour
        self.AR = AR

        
    @classmethod
    def of_ligne(cls, ligne, g):
        """ Entrée : ligne (str), une ligne de csv du questionnaire. Les colonnes sont séparées par | . Il y a 12 colonnes, les 9 premières sont inutiles.
                     g (Graphe). Utilisé pour déterminer le nœud associé à chaque étape.
        """
        données = list(map(sans_guillemets, ligne.strip().split("|")[9:]))
        assert len(données)==3, f"Pas le bon nombre de colonnes dans la ligne {ligne}."
        print(données)
        p_détour = float(données[1])/100
        étapes = [g.un_nœud_sur_rue(étape) for étape in données[2].split(";")]
        if données[0] == "oui": AR = True
        else: AR = False
        return cls(étapes, p_détour, AR)

    @classmethod
    def of_étapes(cls, étapes, pourcentage_détour, AR, g):
        """Plutôt pour rentrer à la main un chemin.
        Entrées : étapes (str list).
                  pourcentage_détour (int)
                  AR (bool)
                  g (Graphe)
        """
        id_étapes = [g.un_nœud_sur_rue(é) for é in étapes]
        return cls(id_étapes, pourcentage_détour/100, AR)
        
    
    def départ(self):
        return self.étapes[0]
    def arrivée(self):
        return self.étapes[-1]

    def renversé(self):
        assert self.AR, "chemin pas réversible"
        return Chemin(list(reversed(self.étapes)), self.p_détour, self.AR)
    
    def __str__(self):
        return ";".join(map(string,self.étapes))

   
def chemins_of_csv(adresse_csv, g):
    entrée = open(adresse_csv)
    #res=[g.chemin_of_string(ligne) for ligne in entrée ]
    res=[]
    for ligne in entrée:
        try:
            chemin = Chemin.of_ligne(ligne, g)
            res.append(chemin)
        except Exception as e:
            print(e)
            print(f"Chemin abandonné : {ligne}")
    entrée.close()
    return res
