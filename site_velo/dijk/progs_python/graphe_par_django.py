# -*- coding:utf-8 -*-

from dijk.models import Rue, Ville
import recup_donnees as rd
from params import LOG

class Graphe_django():
    def __init__(self):
        pass
    

    def nœuds_of_rue(self, adresse, bavard=0):
        """
        Entrées : adresse (Adresse)
        Sortie : la liste des nœuds pour la rue indiquée.
                 Essai 1 : recherche dans la base (utilise adresse.rue_norm)
                 Essai 2 : via Nominatim et overpass, par recup_donnees.nœuds_of_rue
        """
        
        try:
            # Essai 1 : dans la base
            v = Ville.objects.get(nom_norm=adresse.ville.nom_norm)
            r = Rue.objects.get(nom_norm=adresse.rue_norm, ville=v)
            res = r.nœuds()
            print(f"Trouvé {list(res)} pour {adresse}")
            return res
        
        except Exception as e:
            LOG(f"(graphe_par_django.nœuds_of_rue) Rue pas en mémoire : {adresse} (erreur reçue : {e}), je lance recup_donnees.nœuds_of_rue", bavard=bavard)
            # Essai 2 : via rd.nœuds_of_rue, puis intersection avec les nœuds de g
            res = [ n for n in rd.nœuds_of_rue(adresse) if n in self]
            LOG(f"nœuds trouvés : {res}", bavard=bavard)
            if len(res)>0:
                self.ajoute_rue(adresse, res, bavard=bavard)
            return res

        
    def ajoute_rue(self, adresse, nœuds, bavard=0):
        """
        Effet : ajoute la rue dans la base si elle n'y est pas encore.
        """
        LOG(f"J'ajoute la rue {adresse} dans la base. Nœuds : {nœuds}", bavard=1)
        ville_d = Ville.objects.get(nom_norm=adresse.ville.nom_norm)
        try:
            r = Rue.objects.get(nom_norm=adresse.rue_norm, ville=ville_d)
            LOG(f"rue déjà présente : {r}", bavard=bavard+1)
        except Exception as e:
            nœuds_à_découper = ",".join(map(str, nœuds))
            rue_d = Rue(nom_complet=adresse.rue, nom_norm=adresse.rue_norm, ville=ville_d, nœuds_à_découper=nœuds_à_découper)
            rue_d.save()
