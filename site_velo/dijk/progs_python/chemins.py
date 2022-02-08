# -*- coding:utf-8 -*-
from time import perf_counter
from petites_fonctions import chrono

from params import LOG_PB, CHEMIN_CHEMINS, DONNÉES, LOG
from dijk.models import Sommet, Chemin_d

tic=perf_counter()
from recup_donnees import cherche_lieu, coords_of_adresse
chrono(tic, "recup_donnees")
#import module_graphe
import os
tic=perf_counter()
from lecture_adresse.normalisation import normalise_adresse, normalise_rue, normalise_ville
chrono(tic, "lecture_adresse.normalisation")
import re
import dijkstra
tic=perf_counter()
from lecture_adresse.recup_noeuds import nœuds_of_étape
chrono(tic, "lecture_adresse.recup_noeuds")
#Pour test
#import init_graphe
#g = init_graphe.charge_graphe(bavard=1)


def sans_guillemets(c):
    if c[0] == '"':
        assert c[-1] == '"', f"Guillemets pas comme prévu, dans la chaîne {c}"
        return c[1:-1]
    else:
        return c

    
class ÉchecChemin(Exception):
    pass


class Étape():
    """
    Attributs : 
        texte (str), adresse de l'étape. 
        adresse (instance de Adresse)
        nœuds (Sommet set) : ensemble de nœuds
    """
    
    def __init__(self, texte, g, z_d, bavard=0):
        self.texte = texte
        n, self.adresse = nœuds_of_étape(texte, g, z_d, bavard=bavard-1)
        self.nœuds = set(n)
        #for n in self.nœuds:
        #    assert n in g, f"J’ai obtenu un nœud qui n’est pas dans le graphe en lisant l’étape {texte} : {n}"
        
    def __str__(self):
        return str(self.adresse)


def dico_arête_of_nœuds(g, nœuds):
    """
    Entrée : nœuds (Sommet iterable), un ensemble de sommets
    Sortie : dictionnaire (s -> voisins de s qui sont dans nœuds)
    """
    return {
        s: set((t for t in g.voisins_nus(s) if t in nœuds))
        for s in nœuds
    }


def arêtes_interdites(g, z_d, noms_rues, bavard=0):
    """
    Entrée : g (graphe)
             z_d (Zone)
             noms_rues (str iterable), liste de noms de rues à éviter
    Sortie : dico des arêtes correspondant
    """
    interdites = {}
    for r in noms_rues:
        interdites.update(
            dico_arête_of_nœuds(g,
                                nœuds_of_étape(r, g, z_d, bavard=bavard)[0]
            )
        )
    return interdites


class Chemin():
    """ Attributs : - p_détour (float)
                    - étapes (Étape list), liste de nœuds
                    - interdites : arêtesi interdites. dico s->sommets interdits depuis s
                    - noms_rues_interdites : str, noms des rues interdites séparées par ; (pour l’enregistrement en csv)
                    - AR (bool), indique si le retour est valable aussi.
                    - texte (None ou str), texte d'où vient le chemin (pour déboguage)
                    - zone (models.Zone)
    """
    def __init__(self, z_d, étapes, p_détour, AR, interdites={}, texte_interdites=""):
        assert p_détour>=0 and p_détour<=2, "Y aurait-il confusion entre la proportion et le pourcentage de détour?"
        self.étapes = étapes
        self.p_détour = p_détour
        self.AR = AR
        self.texte = None
        self.interdites=interdites
        self.noms_rues_interdites=texte_interdites
        self.zone=z_d
    

    @classmethod
    def of_django(cls, c_d, g, bavard=0):
        return cls.of_données(g, c_d.zone, c_d.ar, c_d.p_détour, c_d.étapes_texte, c_d.interdites_texte, bavard=bavard)

    
    def vers_django(self, utilisateur=None, bavard=0):
        """
        Transfert le chemin dans la base.
        Sortie : l’instance de Chemin_d créée.
        """
        étapes_t = ";".join(map(str, self.étapes))
        rues_interdites_t=self.noms_rues_interdites
        début, fin = étapes_t[:255], étapes_t[-255:]
        interdites_début, interdites_fin = rues_interdites_t[:255], rues_interdites_t[-255:]

        test = Chemin_d.objects.filter(p_détour = self.p_détour, ar=self.AR, début=début, fin = fin, interdites_début=interdites_début, interdites_fin=interdites_fin)
        if test.exists():
            LOG(f"Chemin déjà dans la base : {self}")
            return test.first()
        else:
            c_d = Chemin_d(
                p_détour = self.p_détour, ar=self.AR, étapes_texte=étapes_t, interdites_texte=rues_interdites_t, utilisateur=utilisateur,début=début, fin = fin, interdites_début=interdites_début, interdites_fin=interdites_fin,
                zone=self.zone
            )
            c_d.save()
            return c_d

    
    @classmethod
    def of_ligne(cls, ligne, g, tol=.25, bavard=0):
        """ Entrée : ligne (str), une ligne du csv de chemins. Format AR|pourcentage_détour|étapes|rues interdites.
                     g (Graphe). Utilisé pour déterminer les nœuds associés à chaque étape.
        tol indique la proportion tolérée d’étapes qui n’ont pas pu être trouvées.
        """

        ## Extraction des données
        AR_t, pourcentage_détour_t, étapes_t,rues_interdites_t = ligne.strip().split("|")
        p_détour = int(pourcentage_détour_t)/100.
        AR = bool(AR_t)
        return cls.of_données(g, AR, p_détour, étapes_t, rues_interdites_t, bavard=bavard)

        
    @classmethod
    def of_données(cls, g, z_d, AR, p_détour, étapes_t, rues_interdites_t, bavard=0):
        """
        Entrée :
            - AR (bool)
            - p_détour (float)
            - étapes_t (str) : étapes séparées par ;
            - rues_interdites_t (str) : rues interdites, séparées par ;
        """
        
        #rues interdites
        if len(rues_interdites_t)>0:
            noms_rues = rues_interdites_t.split(";")
            interdites = arêtes_interdites(g, z_d, noms_rues, bavard=bavard)
        else:
            interdites = {}
        
        # étapes 
        noms_étapes = étapes_t.split(";")
        n_pb = 0
        étapes=[]
        for c in noms_étapes:
        #    try:                
                étapes.append(Étape(c.strip(), g, z_d, bavard=bavard-1))
        #     except Exception as e:
        #         LOG_PB(f"Échec pour l’étape {c} : {e}")
        #         n_pb+=1
        # if n_pb/len(noms_étapes) > tol:
        #     raise ÉchecChemin(f"{n_pb} erreurs pour la lecture de {ligne}.")

        
        ## Création de l’objet Chemin
        chemin = cls(z_d, étapes, p_détour, AR, interdites=interdites, texte_interdites=rues_interdites_t)
        chemin.texte = étapes_t
        return chemin


    def sauv_bdd(self):
        """
        Enregistre le chemin dans la base.
        """
        c = Chemin_d(p_détour=self.p_détour,
                   étapes=";".join(map(str, self.étapes)),
                   ar=self.AR,
                   interdites=self.noms_rues_interdites,
                   )
        c.sauv()
    
    @classmethod
    def of_étapes(cls, z_d, noms_étapes, pourcentage_détour, AR, g, noms_rues_interdites=[], bavard=0):
        """
        Entrées : noms_étapes (str list).
                  pourcentage_détour (int)
                  AR (bool)
                  g (Graphe)
        Sortie : instance de Chemin
        """
        étapes = [Étape(é, g, z_d) for é in noms_étapes]
        if bavard>0:
            print(f"List des étapes obtenues : {étapes}")
        
        return cls(z_d, étapes, pourcentage_détour/100, AR,
                   interdites=arêtes_interdites(g, z_d, noms_rues_interdites),
                   texte_interdites=";".join(noms_rues_interdites)
                   )
    
    
    def départ(self):
        return self.étapes[0]
    def arrivée(self):
        return self.étapes[-1]

    def renversé(self):
        assert self.AR, "chemin pas réversible (AR est faux)"
        return Chemin(self.zone, list(reversed(self.étapes)), self.p_détour, self.AR)

    def chemin_direct_sans_cycla(self, g):
        """ Renvoie le plus court chemin du départ à l’arrivée."""
        return dijkstra.chemin_entre_deux_ensembles(g, self.départ(), self.arrivée(), 0)
    
    def direct(self):
        """ Renvoie le chemin sans ses étapes intermédaires."""
        
        return Chemin([self.départ(), self.arrivée()], self.p_détour, True)
    
    def __str__(self):
        res = f"AR : {self.AR}\np_détour : {self.p_détour}\nÉtapes : " + ";".join(map(str, self.étapes))
        if self.noms_rues_interdites: res+=f"\n Rues interdites : {self.noms_rues_interdites}"
        return  res

    def str_joli(self):
        res = f"Itinéraire de {self.départ()} à {self.arrivée()}"
        milieu = self.étapes[1:-1]
        if milieu:
            res+= f" en passant par {','.join(map(str,milieu))}"
        if self.noms_rues_interdites:
            res+=f" et en évitant {','.join(self.noms_rues_interdites)}"
        return res+"."
        

    def texte_court(self, n_étapes=4):
        if len(self.étapes) <= n_étapes:
            return str(self)
        else:
            à_garder = self.étapes[0:-1:len(self.étapes)//n_étapes] + [self.étapes[-1]]
            return ";".join(map(str, à_garder))

   
def chemins_of_csv(g, adresse_csv=CHEMIN_CHEMINS, bavard=0):
    """
    Renvoie la liste des chemins contenus dans le csv.
    """
    entrée = open(adresse_csv, encoding="utf-8")
    #res=[g.chemin_of_string(ligne) for ligne in entrée ]
    res = []
    for ligne in entrée:
        try:
            chemin = Chemin.of_ligne(ligne, g, bavard=bavard)
            res.append(chemin)
        except Exception as e:
            LOG_PB( f"{e}\n Chemin abandonné : {ligne}\n" )
    entrée.close()
    return res


# def formulaire_vers_csv(ad_entrée=os.path.join(DONNÉES,"chemins_form.csv"), ad_sortie = CHEMIN_CHEMINS ):
#     """ 
#     Entrées : adresse d’un csv issu du framaform
#               autre adresse
#     Effet : copie une version nettoyée du csv initial dans l’adresse de sortie. Format utilisé : AR|pourcentage_détour|étapes séparées par des ;
#     """
#     def bool_of_text(t):
#         if t=="oui":
#             return True
#         elif t=="non":
#             return False
#         else:
#             raise ValueError(f"J’attendais 'oui' ou 'non' mai j’ai eu {t}.")
#     entrée = open(ad_entrée, encoding="utf-8")
#     sortie = open(ad_sortie,"w", encoding="utf-8")
#     for ligne in entrée:
#         données = list(map(sans_guillemets, ligne.strip().split("|")[9:]))
#         assert len(données) == 3, f"Pas le bon nombre de colonnes dans la ligne {ligne}."
#         données[0]=str(bool_of_text(données[0]))
#         ligne = "|".join(données)
#         print("\n", ligne)
#         sortie.write(ligne+"\n")


def lecture_étape(c):
    """ Entrée : chaîne de caractère représentant une étape.
        Sortie : nom de rue, ville, pays
    """
    e = re.compile("([^()]*)(\(.*\))")  # Un texte puis un texte entre parenthèses
    essai1 = re.findall(e, c)
    if len(essai1) > 0:
        rue, ville = essai1[0]
        return rue.strip(), ville[1:-1].strip()  # retirer les parenthèses
    else:
        f = re.compile("^[^()]*$")  # Pas de parenthèse du tout
        if re.findall(f, c):
            return c.strip(), VILLE_DÉFAUT
        else:
            raise ValueError(f"chaîne pas correcte : {c}")



