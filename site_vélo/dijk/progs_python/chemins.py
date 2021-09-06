# -*- coding:utf-8 -*-

from dijk.progs_python.params import LOG_PB, CHEMIN_CHEMINS, DONNÉES
from récup_données import cherche_lieu, coords_lieu, coords_of_adresse
import module_graphe
import os
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
        texte (str), adresse de l'étape. 
        adresse (instance de Adresse)
        nœuds (int set) : ensemble de nœuds
    """
    def __init__(self, texte, g, bavard=0):
        self.texte = texte
        n, self.adresse = nœuds_of_étape(texte, g, bavard=bavard-1)
        self.nœuds = set(n)
        for n in self.nœuds:
            assert n in g, f"J’ai obtenu un nœud qui n’est pas dans le graphe en lisant l’étape {texte} : {n}"

    def __str__(self):
        return str(self.adresse)


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
        """ Entrée : ligne (str), une ligne du csv de chemins. Format AR|pourcentage_détour|étapes.
                     g (Graphe). Utilisé pour déterminer le nœud associé à chaque étape.
        tol indique la proportion tolérée d’étapes qui n’ont pas pu être trouvées.
        """

        AR_t, pourcentage_détour_t, étapes_t = ligne.strip().split("|")
        p_détour = int(pourcentage_détour_t)/100.
        AR = bool(AR_t)
        
        noms_étapes = étapes_t.split(";")
        n_pb = 0
        étapes=[]
        for c in noms_étapes:
            try:
                étapes.append(Étape(c.strip(), g, bavard=bavard-1))
            except Exception as e:
                LOG_PB(f"Échec pour l’étape {c} : {e}")
                n_pb+=1
        if n_pb/len(noms_étapes) > tol:
            raise ÉchecChemin(f"{n_pb} erreurs pour la lecture de {ligne}.")
        
        chemin = cls(étapes, p_détour, AR)
        chemin.texte = étapes_t
        return chemin

    
    def sauv(self, adresse=CHEMIN_CHEMINS):
        """ Ajoute le chemin dans le csv, après avoir vérifié qu’il n’y est pas déjà."""
            
        ligne = f"{self.AR}|{int(self.p_détour*100)}|{ ';'.join(map(str, self.étapes)) }\n"
        
        with open(adresse) as entrée:
            for ligne_e in entrée:
                if ligne_e==ligne:
                    print(f"Ligne déjà présente : {ligne}")
                    return None
                
        with open(adresse, "a") as sortie:
            sortie.write(ligne)
    
    @classmethod
    def of_étapes(cls, noms_étapes, pourcentage_détour, AR, g, bavard=0):
        """
        Plutôt pour rentrer à la main un chemin.
        Entrées : noms_étapes (str list).
                  pourcentage_détour (int)
                  AR (bool)
                  g (Graphe)
        """
        étapes = [Étape(é, g) for é in noms_étapes]
        if bavard>0:
            print(f"List des étapes obtenues : {étapes}")
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

   
def chemins_of_csv(g, adresse_csv=CHEMIN_CHEMINS, bavard=0):
    """
    Renvoie la liste des chemins contenus dans le csv.
    """
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


def formulaire_vers_csv(ad_entrée=os.path.join(DONNÉES,"chemins_form.csv"), ad_sortie = CHEMIN_CHEMINS ):
    """ 
    Entrées : adresse d’un csv issu du framaform
              autre adresse
    Effet : copie une version nettoyée du csv initial dans l’adresse de sortie. Format utilisé : AR|pourcentage_détour|étapes séparées par des ;
    """
    def bool_of_text(t):
        if t=="oui":
            return True
        elif t=="non":
            return False
        else:
            raise ValueError(f"J’attendais 'oui' ou 'non' mai j’ai eu {t}.")
    entrée = open(ad_entrée)
    sortie = open(ad_sortie,"w")
    for ligne in entrée:
        données = list(map(sans_guillemets, ligne.strip().split("|")[9:]))
        assert len(données) == 3, f"Pas le bon nombre de colonnes dans la ligne {ligne}."
        données[0]=str(bool_of_text(données[0]))
        ligne = "|".join(données)
        print("\n", ligne)
        sortie.write(ligne+"\n")


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



