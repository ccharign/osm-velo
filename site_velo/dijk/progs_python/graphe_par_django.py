# -*- coding:utf-8 -*-

from dijk.models import Rue, Ville, Arête, Sommet
import recup_donnees as rd
from params import LOG
from petites_fonctions import deuxConséc, chrono, distance_euc
from time import perf_counter
from django.db.models import Max, Min


class Graphe_django():
    """
    Cette classe sert d'interface avec la base Django.
    Attribut: 
        dico_voisins (dico int -> (int, float, float) list) associe à un id_osm la liste de ses (voisins, distance, cycla)
        dico_coords (dico int->(float,float)) associe (lon,lat) à chaque id_osm
    """
    
    def __init__(self):

        # Arêtes
        tic=perf_counter()
        self.dico_voisins={}
        for a in Arête.objects.all().select_related("départ", "arrivée"):
            s = a.départ.id_osm
            t = a.arrivée.id_osm
            if s not in self.dico_voisins: self.dico_voisins[s]=[]
            self.dico_voisins[s].append((t, a.longueur, a.cyclabilité()))
        tic=chrono(tic, "Chargement de dico_voisins depuis la base de données.")

        #Sommets
        self.dico_coords={}
        for s in Sommet.objects.all():
            self.dico_coords[s.id_osm] = s.coords()
        tic=chrono(tic, "Chargement des coords des sommets (pour A*)")

        #cycla min et max
        self.cycla_min = Arête.objects.all().aggregate(Min("cycla"))["cycla__min"]
        self.cycla_max = Arête.objects.all().aggregate(Max("cycla"))["cycla__max"]
        chrono(tic, "calcul cycla min et max")

        
    def __contains__(self, s):
        """
        Entrée : s (int)
        Sortie : il existe un sommet d'identifiant osm s dans la base.
        """
        return Sommet.objects.filter(id_osm=s).exists()

    
    def coords_of_Sommet(self, s):
        return s.coords()

    def coords_of_id_osm(self, s):
        #return Sommet.objects.get(id_osm=s).coords()
        return self.dico_coords[s]

    def d_euc(self, s, t):
        cs, ct = self.coords_of_id_osm(s), self.coords_of_id_osm(t)
        return distance_euc(cs, ct)

    
    def longueur_corrigée(self, l, cy, p_détour):
        """
        La formule pour prendre en compte la cyclabilité.
        Actuellement : l / cy**(p_détour*1.5)
        """
        return l / cy**(p_détour*1.5)

    
    def meilleure_arête(self, s, t, p_détour):
        """
        Échoue si deux arêtes ont mêmes départ, arrivée, et longueur...
        """
        #arêtes = Arête.objects.filter(départ__id_osm=s, arrivée__id_osm=t)
        données = [(l, cy) for (v, l, cy) in self.dico_voisins[s] if v==t]
        _, l, cy = min( (self.longueur_corrigée(l, cy, p_détour), l, cy) for (l,cy) in données )
        return Arête.objects.get(départ__id_osm=s, arrivée__id_osm=t, longueur=l)

    def longueur_meilleure_arête(self, s, t, p_détour):
        longueurs = (l for (v,l) in self.voisins(s, p_détour) if v==t)
        return min(longueurs)
        
    def geom_arête(self, s, t, p_détour):
        """
        Renvoie la géométrie de la plus courte arête de s à t, compte tenu de la proportion de détour indiquée.
        """
        a = self.meilleure_arête(s, t, p_détour)
        return a.géométrie(), a.nom

    
    def longueur_itinéraire(self, iti, p_détour):
        """
        Entrée : iti (Sommet list)
                 p_détour (float)
        Renvoie la vraie longueur de l'itinéraire. p_détour sert à choisir l'arête en cas de multiarête.
        """
        res = 0.
        #iti_d = [Sommet.objects.get(id_osm=s) for s in iti]
        for s,t in deuxConséc(iti):
            res += self.longueur_meilleure_arête(s,t,p_détour)
        return res


    def tous_les_nœuds(self):
        return Sommet.objects.all()


    

        
    def voisins(self, s, p_détour, interdites={}):
        """
        Entrées :
            - s (int)
            - p_détour (float), proportion de détour accepté.
            - interdites (dico Sommet -> liste de Sommets), arêtes interdites.

        La méthode utilisée par dijkstra. Renvoie les couples (voisin, longueur de l'arrête) issus du sommet s.
        La longueur de l'arrête (s, t) renvoyée est sa longueur physique divisée par sa cyclabilité**(p_détour*1.5).
        """
        tout = [ (t, self.longueur_corrigée(l, cy, p_détour) ) for (t,l,cy) in self.dico_voisins[s]]
        if s in interdites:
            return [(t,l) for (t,l) in tout if t not in interdites[s]]
        else:
            return tout

    def voisins_nus(self, s):
        return [t for (t,_,_) in self.dico_voisins[s]]

        
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
