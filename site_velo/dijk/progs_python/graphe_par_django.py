# -*- coding:utf-8 -*-

from dijk.models import Rue, Ville, Arête, Sommet, Cache_Adresse, Zone
import recup_donnees as rd
from params import LOG
from petites_fonctions import deuxConséc, chrono, distance_euc
from time import perf_counter
from django.db.models import Max, Min
import dijkstra


class Graphe_django():
    """
    Cette classe sert d'interface avec la base Django.
    Attribut: 
        dico_voisins (dico int -> (int, Arête) list) associe à un id_osm la liste de ses (voisins, arête)
        dico_Sommet (dico int->Sommet) associe le sommet à chaque id_osm
    """
    
    def __init__(self, zone="Pau"):
        self.dico_voisins={}
        #cycla min et max
        self.calcule_cycla_min_max()
        #chrono(tic, "calcul cycla min et max", force=True)

    def charge_zone(self, zone="Pau"):
        """
        Charge les données présentes dans la base concernant la zone indiquée.
        """
        zone_d = Zone.objects.get(nom=zone)
        
        # Arêtes
        tic=perf_counter()
        arêtes = Arête.objects.filter(zone=zone_d).select_related("départ", "arrivée")
        for a in arêtes:
            s = a.départ.id_osm
            t = a.arrivée.id_osm
            if s not in self.dico_voisins: self.dico_voisins[s]=[]
            self.dico_voisins[s].append((t, a))
        tic=chrono(tic, f"Chargement de dico_voisins depuis la base de données pour la zone {zone}.")

        #Sommets
        self.dico_Sommet={}
        for s in Sommet.objects.filter(zone=zone_d):
            self.dico_Sommet[s.id_osm] = s
        tic=chrono(tic, "Chargement des sommets")


        
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
        return self.dico_Sommet[s].coords()

    def d_euc(self, s, t):
        cs, ct = self.coords_of_id_osm(s), self.coords_of_id_osm(t)
        return distance_euc(cs, ct)

    


    
    def meilleure_arête(self, s, t, p_détour):
        """
        Renvoie l'arête (instance d'Arête) entre s et t de longueur corrigée minimale.
        """
        #arêtes = Arête.objects.filter(départ__id_osm=s, arrivée__id_osm=t)
        données = ((a.longueur_corrigée(p_détour), a) for (v, a) in self.dico_voisins[s] if v==t)
        _, a = min(données)
        return a

    def longueur_meilleure_arête(self, s, t, p_détour):
        longueurs = (a.longueur_corrigée(p_détour) for (v, a) in self.dico_voisins[s] if v==t)
        return min(longueurs)
        
    def geom_arête(self, s, t, p_détour):
        """
        Renvoie la géométrie de la plus courte arête de s à t, compte tenu de la proportion de détour indiquée.
        """
        a = self.meilleure_arête(s, t, p_détour)
        return a.géométrie(), a.nom

    def incr_cyclabilité(self, a, p_détour, dc):
        """ 
        Augmente la cyclabilité de l'arête a (couple de nœuds), ou l'initialise si elle n'était pas encore définie.
        Met à jour self.cycla_max si besoin
        Formule appliquée : *= (1+dc)
        """
        s,t = a
        a_d = self.meilleure_arête(s, t, p_détour)
        a_d.incr_cyclabilité(dc)
        a_d.save()
        #self.cycla_max = max(self.cycla_max, a_d.cycla)

    def calcule_cycla_min_max(self):
        
        self.cycla_min = Arête.objects.aggregate(Min("cycla"))["cycla__min"]
        if self.cycla_min is None:
            self.cycla_min=1.

        self.cycla_max = Arête.objects.aggregate(Max("cycla"))["cycla__max"]
        if self.cycla_max is None:
            self.cycla_max=1.
            
        print(f"Cycla min et max : {self.cycla_min}, {self.cycla_max}")
        
    def liste_Arête_of_iti(self, iti, p_détour):
        return [self.meilleure_arête(s,t,p_détour) for (s,t) in deuxConséc(iti)]

    def itinéraire(self, chemin, bavard=0):
        """
        Entrée : chemin (Chemin)
        Sortie : iti_d, l_ressentie (liste d'Arêtes, float)
        """
        iti, l_ressentie = dijkstra.chemin_étapes_ensembles(self, chemin, bavard=bavard)
        return self.liste_Arête_of_iti(iti, chemin.p_détour), l_ressentie
    
    # def longueur_itinéraire(self, iti, p_détour):
    #     """
    #     Entrée : iti (Sommet list)
    #              p_détour (float)
    #     Renvoie la vraie longueur de l'itinéraire. p_détour sert à choisir l'arête en cas de multiarête.
    #     """
    #     res = 0.
    #     #iti_d = [Sommet.objects.get(id_osm=s) for s in iti]
    #     for s,t in deuxConséc(iti):
    #         res += self.longueur_meilleure_arête(s,t,p_détour)
    #     return res
    def longueur_itinéraire(self, iti_d):
        """
        Entrée : iti_d (Arête list)
        Sortie : la vraie longueur de l'itinéraire.
        """
        return sum(a.longueur for a in iti_d)


    def tous_les_nœuds(self):
        return Sommet.objects.all()


    

        
    def voisins(self, s, p_détour, interdites={}):
        """
        La méthode utilisée par dijkstra.
        Entrées :
            - s (int)
            - p_détour (float), proportion de détour accepté.
            - interdites (dico Sommet -> liste de Sommets), arêtes interdites.

        La méthode utilisée par dijkstra. Renvoie les couples (voisin, longueur de l'arrête) issus du sommet s.
        La longueur de l'arrête (s, t) renvoyée est sa longueur physique divisée par sa cyclabilité**(p_détour*1.5).
        """
        tout = [ (t, a.longueur_corrigée(p_détour) ) for (t, a) in self.dico_voisins[s]]
        if s in interdites:
            return [(t,l) for (t,l) in tout if t not in interdites[s]]
        else:
            return tout

    def voisins_nus(self, s):
        return [t for (t,_) in self.dico_voisins[s]]

        
    def nœuds_of_rue(self, adresse, bavard=0):
        """
        Entrées : adresse (Adresse)
        Sortie : la liste des nœuds pour la rue indiquée.
                 Essai 1 : recherche dans la base (utilise adresse.rue_norm)
                 Essai 2 : via Nominatim et overpass, par recup_donnees.nœuds_of_rue. Ceci récupère les nœuds des ways renvoyés par Nominatim.
                    En cas d'essai 2 concluant, le résultat est rajouté dans la table des Rues.
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

            
    def met_en_cache(self, adresse, res):
        ligne = Cache_Adresse(adresse=str(adresse), nœuds_à_découper = ",".join(map(str,res)))
        ligne.save()
        LOG(f"Mis en cache : {res} pour {adresse}", bavard=1)

    def dans_le_cache(self, adresse):
        res = Cache_Adresse.objects.filter(adresse=str(adresse))
        if len(res)==1:
            return res[0].nœuds()
        elif len(res)>1:
            LOG_PB(f"Plusieurs valeurs en cache pour {adresse}")
