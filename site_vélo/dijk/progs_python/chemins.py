# -*- coding:utf-8 -*-

from récup_données import cherche_lieu, coords_lieu, coords_of_adresse
import module_graphe
from params import LOG_PB
from lecture_adresse.normalisation import VILLE_DÉFAUT
import re
import dijkstra
from lecture_adresse.normalisation import normalise_adresse, normalise_rue, normalise_ville
from lecture_adresse.récup_nœuds import nœuds_of_étape
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
        texte (str), adresse de l'étape
        nœuds (int set) : ensemble de nœuds
    """
    def __init__(self, adresse, g, bavard=0):
        self.texte = adresse
        self.nœuds = set(nœuds_of_étape(adresse, g, bavard=bavard-1))
        for n in self.nœuds:
            assert n in g.digraphe.nodes, f"J’ai obtenu un nœud qui n’est pas dans le graphe en lisant l’étape {adresse} : {n}"

    def __str__(self):
        return self.texte


class Chemin():
    """ Attributs : - p_détour (float)
                    - étapes (Étape list), liste de nœuds
                    - AR (bool), indique si le retour est valable aussi.
                    - texte (None ou str), texte d'où vient le chemin (pour déboguage)
    """
    def __init__(self, étapes, p_détour, AR):
        assert p_détour>=0 and p_détour<=2, "Y aurait-il confusion entre la proportion et le pourcentage de détour?"
        self.étapes = étapes
        self.p_détour = p_détour
        self.AR = AR
        self.texte = None
    
    
    @classmethod
    def of_ligne(cls, ligne, g, tol=.25, bavard=0):
        """ Entrée : ligne (str), une ligne de csv du questionnaire. Les colonnes sont séparées par | . Il y a 12 colonnes, les 9 premières sont inutiles.
                     g (Graphe). Utilisé pour déterminer le nœud associé à chaque étape.
        tol indique la proportion tolérée d’étapes qui n’ont pas pu être trouvées.
        """
        données = list(map(sans_guillemets, ligne.strip().split("|")[9:]))
        assert len(données) == 3, f"Pas le bon nombre de colonnes dans la ligne {ligne}."
        print("\n", données)
        p_détour = float(données[1])/100.
        
        étapes = []
        noms_étapes = données[2].split(";")
        n_pb = 0
        for c in noms_étapes:
            try:
                étapes.append(Étape(c, g, bavard=bavard-1))
            except Exception as e:
                LOG_PB(f"Échec pour l’étape {c}")
                n_pb+=1
        if n_pb/len(noms_étapes) > tol:
            raise ÉchecChemin(f"{n_pb} erreurs pour la lecture de {données}.")
        
            
        if données[0] == "oui": AR = True
        else: AR = False
        
        chemin = cls(étapes, p_détour, AR)
        chemin.texte = (données[2])
        return chemin

    @classmethod
    def of_étapes(cls, noms_étapes, pourcentage_détour, AR, g):
        """Plutôt pour rentrer à la main un chemin.
        Entrées : noms_étapes (str list).
                  pourcentage_détour (int)
                  AR (bool)
                  g (Graphe)
        """
        étapes = [Étape(é, g) for é in noms_étapes]
        return cls(étapes, pourcentage_détour/100, AR)
    
    
    def départ(self):
        return self.étapes[0]
    def arrivée(self):
        return self.étapes[-1]

    def renversé(self):
        assert self.AR, "chemin pas réversible"
        return Chemin(list(reversed(self.étapes)), self.p_détour, self.AR)

    def chemin_direct_sans_cycla(self, g):
        """ Renvoie le plus court chemin du départ à l’arrivée."""
        return dijkstra.chemin_entre_deux_ensembles(g, self.départ(), self.arrivée(), 0)
    
    def direct(self):
        """ Renvoie le chemin sans ses étapes intermédaires."""
        
        return Chemin([self.départ(), self.arrivée()], self.p_détour, True)
    
    def __str__(self):
        if self.texte is not None:
            return self.texte
        else:
            return ";".join(map(str, self.étapes))

    def texte_court(self, n_étapes=4):
        if len(self.étapes) <= n_étapes:
            return str(self)
        else:
            à_garder = self.étapes[0:-1:len(self.étapes)//n_étapes] + [self.étapes[-1]]
            return ";".join(map(str, à_garder))

   
def chemins_of_csv(g, adresse_csv="données/chemins.csv", bavard=0):
    entrée = open(adresse_csv)
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



