# -*- coding:utf-8 -*-

from récup_données import cherche_lieu, coords_lieu, coords_of_adresse
import module_graphe
from params import LOG_PB
from lecture_adresse.normalisation import VILLE_DÉFAUT
import re
import dijkstra
from lecture_adresse.normalisation import normalise_adresse, normalise_rue, normalise_ville

#Pour test
#import init_graphe
#g = init_graphe.charge_graphe(bavard=1)


def sans_guillemets(c):
    if c[0] == '"':
        assert c[-1] == '"', f"Guillemets pas comme prévu, dans la chaîne {c}"
        return c[1:-1]
    else:
        return c


class Étape():
    """
    Attributs : 
        texte (str), adresse de l'étape
        nœuds (int set) : ensemble de nœuds
    """
    def __init__(self, adresse, g, bavard=0):
        self.texte = adresse
        self.nœuds = set(nœud_of_étape(adresse, g, bavard=bavard-1))
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
        self.étapes = étapes
        self.p_détour = p_détour
        self.AR = AR
        self.texte = None
    
    
    @classmethod
    def of_ligne(cls, ligne, g):
        """ Entrée : ligne (str), une ligne de csv du questionnaire. Les colonnes sont séparées par | . Il y a 12 colonnes, les 9 premières sont inutiles.
                     g (Graphe). Utilisé pour déterminer le nœud associé à chaque étape.
        """
        données = list(map(sans_guillemets, ligne.strip().split("|")[9:]))
        assert len(données) == 3, f"Pas le bon nombre de colonnes dans la ligne {ligne}."
        print("\n", données)
        p_détour = float(données[1])/100.
        étapes = []
        for c in données[2].split(";"):
            étapes.append(Étape(c, g))
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

   
def chemins_of_csv(g, adresse_csv="données/chemins.csv"):
    entrée = open(adresse_csv)
    #res=[g.chemin_of_string(ligne) for ligne in entrée ]
    res = []
    for ligne in entrée:
        try:
            chemin = Chemin.of_ligne(ligne, g)
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




def nœud_of_étape(c, g, bavard=0):
    """ c : chaîne de caractères décrivant une étape. Optionnellement un numéro devant le nom de la rue, ou une ville entre parenthèses.
        g : graphe.
        Sortie : liste de nœuds de g associé à cette adresse.
           Si un numéro est indiqué, renvoie le singleton du nœud de la rue le plus proche.
           Sinon renvoie la liste des nœuds de la rue."""

    c = normalise_adresse(c)
    assert c != ""
    
    if c in g.nœud_of_rue:  # Recherche dans le cache
        if bavard : print(f"Adresse dans le cache : {c}")
        return g.nœud_of_rue[c]
    else:
        print(f"Pas dans le cache : {c}")
    
    def renvoie(res):
        assert res != []
        assert all(isinstance(s, int) and s in g.digraphe.nodes for s in res)
        g.nœud_of_rue[c] = res
        print(f"Mis en cache : {res} pour {c}")
        return res

    
    ## Analyse de l’adresse. On récupère les variables num, rue, ville
    e = re.compile("(^[0-9]*)([^()]+)(\((.*)\))?")
    essai = re.findall(e, c)
    if bavard > 1: print(f"Résultat de la regexp : {essai}")
    if len(essai) == 1:
        num, rue, _, ville = essai[0]
    elif len(essai) == 0:
        raise SyntaxError(f"adresse mal formée : {c}")
    else:
        print(f"Avertissement : plusieurs interprétations de {c} : {essai}.")
        num, rue, _, ville = essai[0]
    rue = normalise_rue(rue.strip())
    
    #if ville == "": ville = VILLE_DÉFAUT
    ville = normalise_ville(ville.strip())
    if bavard>0: print(f"analyse de l’adresse : {num} {rue}, {ville.avec_code()}")
    
    
    if num == "":
    ## Pas de numéro de rue -> liste de tous les nœuds de la rue
        if bavard > 0 : print("Pas de numéro de rue, je vais renvoyer une liste de nœuds")
        if rue == "":
            raise SyntaxError(f"adresse mal formée : {c}")
        else:
            try:
                #res = module_graphe.nœuds_sur_rue(g.digraphe, rue, ville=ville)
                #return renvoie(res)
                res = g.nœuds[str(ville)][rue]
                if bavard > 0: print(f"nœuds trouvés dans g.nœuds[{str(ville)}][{rue}] : {res}.")
                return res
            except KeyError as e:
                print(f"rue pas en mémoire : {rue} ({ville.avec_code()}). Je lance module_graphe.nœuds_sur_rue.")
                res = module_graphe.nœuds_sur_rue(g, rue, ville=VILLE_DÉFAUT, pays="France", bavard=1)
                #coords = coords_lieu(f"{rue}", ville=ville, bavard=bavard-1)
                #print(f"Je vais prendre le nœud le plus proche de {coords}.")
                #n = g.nœud_le_plus_proche(coords)
                return renvoie(res)

            
    else:
        ## Numéro de rue -> renvoyer un singleton
        if bavard >0 : print("Numéro de rue présent : je vais renvoyer un seul nœud")
        try:
            coords = coords_of_adresse(num, rue, ville=ville)
        except Exception as e:
            print(f"Échec dans coords_of_adresse : {e}. Je passe à coords_lieu, càd avec une recherche Nominatim simple.")
            coords = coords_lieu(f"{num} {rue}", ville=ville)
        
        return renvoie([module_graphe.nœud_sur_rue_le_plus_proche(g, coords, rue, ville=ville)])
