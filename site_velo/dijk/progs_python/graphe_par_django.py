# -*- coding:utf-8 -*-

from dijk.models import Rue, Ville

class Graphe_django():
    def __init__(self):
        pass
    

    def nœuds_of_rue(self, ville_n, rue_n):
        """
        Entrées : ville_n, rue_n (str) : noms normalisés d’une ville et d’une rue de celle-ci.
        Sortie : la liste des nœuds en mémoire pour la rue indiquée.
        """
        
        v = Ville.objects.get(nom_norm=ville_n)
        r = Rue.objects.get(nom_norm=rue_n, ville=v)
        res= r.nœuds()
        print(f"Trouvé {list(res)} pour {rue_n}")
        return res
