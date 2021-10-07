
# -*- coding:utf-8 -*-
import re
from params import STR_VILLE_DÉFAUT, PAYS_DÉFAUT, CHEMIN_NŒUDS_RUES
from dijk.progs_python.lecture_adresse.arbresLex import ArbreLex # Arbres lexicographiques et distance d’édition
from initialisation.ajoute_villes import liste_villes



def partie_commune(c):
    """ Appliquée à tout : nom de ville, de rue, et adresse complète
    Met en minuscules
    Supprime les tirets
    Enlève les accents sur les e """
    étape1 = c.strip().lower().replace("-", " ")
    étape2 = re.sub("é|è|ê|ë", "e", étape1)
    return étape2
    

def normalise_adresse(c):
    """ Utilisé pour normaliser les adresses complètes, pour améliorer le cache.
    Actuellement c’est partie_commune(c)"""
    return partie_commune(c)


### Villes ###

print("Création du dico et de l’arbre lex de toutes villes.")
TOUTES_LES_VILLES={
    "Gelos": 64110,
    "Lée": 64320,
    "Pau": 64000,
    "Lescar": 64230,
    "Billère": 64140,
    "Jurançon":64110,
    "Ousse": 64320,
    "Idron": 64320,
    "Lons": 64140 ,
    "Bizanos": 64320,
    "Artigueloutan": 64420
}
ARBRE_VILLES=ArbreLex()
for nom in TOUTES_LES_VILLES.keys():
    ARBRE_VILLES.insère(nom)

class VillePasTrouvée(Exception):
    pass
    
class Ville():
    """
    Attributs :
      - code (int ou None)
      - nom (str) : nom, normalisé par la fonction partie_commune
      - nom_initial (str) : le nom pas encore normalisé
    """
    
    def __init__(self, texte, tol=3):
        """
        Entrée : chaîne de car au format "(code_postal)? nom_ville". Par exemple  ’64000 Pau’ ou ’Bizanos’.
        """

        # Découpage de la chaîne
        e = re.compile("([0-9]{5})? ?([^ 0-9].*)")
        code, nom = re.fullmatch(e, texte.strip()).groups()
        self.nom_initial = nom

        # Récupération du nom de la ville dans l’arbre
        noms_proches=ARBRE_VILLES.mots_les_plus_proches(nom, d_max=tol)
        if len(noms_proches)==0:
            raise VillePasTrouvée(f"Pas trouvé de ville à moins de {tol} fautes de frappe de {nom}. Voici les villes que je connais : {TOUTES_LES_VILLES}.")
        elif len(noms_proches)>1:
            raise VillePasTrouvée(f"Jai plusieurs villes à même distance de {nom}. Il s’agit de {noms_proches}.")
        else:
            nom_corrigé = noms_proches[0]
            code_corrigé = TOUTES_LES_VILLES[nom_corrigé]
            if code is not None and code!= code_corrigé:
                LOG_PB(f"Avertissement : j’ai corrigé le code postal de {code} à {code_corrigé} pour la ville {nom_corrigé}. Chaîne initiale {texte}")
        
        self.nom = partie_commune(nom_corrigé)
        self.code = code_corrigé

    def __str__(self):
        """ Renvoie le nom normalisé."""
        return self.nom

    def avec_code(self):
        if self.code is not None:
            c=str(self.code) + " "
        else:
            c=""
        return f"{c}{self.nom}"


    
VILLE_DÉFAUT = Ville(STR_VILLE_DÉFAUT)




def normalise_ville(ville):
    """
    Actuellement transforme la chaîne de car en un objet de la classe Ville.
    La chaîne vide "" est transformée en VILLE_DÉFAUT (défini dans params.py).
    """
    if ville == "":
        return Ville(STR_VILLE_DÉFAUT)
    else:
        return Ville(ville)


### Rue ###
    

def prétraitement_rue(rue):
    """ 
    Après l’étape "partie_commune", supprime les «de », «du », «de la ».
    Si deux espaces consécutives, supprime la deuxième.
    """
    
    étape1 = partie_commune(rue)
    à_supprimer = [" du ", " de la ", " de ", " d'",  "  "] # Mettre "de la " avant "de ". Ne pas oublier les espaces.
    regexp = "|".join(à_supprimer)
    return re.sub(regexp, " ", étape1)


def créationArbre():
    """ 
    Lit le csv CHEMIN_NŒUDS_RUES, en extrait les noms de toutes les rues et met le tout dans un dictionnaire ville -> arbre des rues.
    rema : dans le csv, les noms des rues et des villes sont supposées avoir l’orthographe d’osm.
    """
    res = {}
    print(f"Chargement de l’arbre des rues depuis {CHEMIN_NŒUDS_RUES}.")
    with open(CHEMIN_NŒUDS_RUES, "r") as entrée:
        for ligne in entrée:
            ville, rue, _ = ligne.strip().split(";")
            ville_n = str(normalise_ville(ville))
            if ville_n not in res: res[ville_n] = ArbreLex()
            res[ville_n].insère(prétraitement_rue(rue))
    return res



ARBRE_DES_RUES = créationArbre()

def normalise_rue(rue, ville, tol=2, bavard=0):
    """
    Entrées : 
      - ville (instance de Ville)
      - rue (str)

    Fonction finale de normalisation d’un nom de rue. Applique partie_commune puis prétraitement_rue puis recherche s’il y a un nom connu à une distance d’édition inférieure à tol (càd à au plus tol fautes de frappe de rue), auquel cas c’est ce nom qui sera renvoyé.
    """
    étape1 = prétraitement_rue(rue)
    res, d =  ARBRE_DES_RUES[ville.nom].mots_les_plus_proches(étape1, d_max=tol)
    if len(res)==1:
        if bavard>0:
            print(f"Nom trouvé à distance {d} de {rue} : {list(res)[0]}")
        return list(res)[0]
    elif len(res)>1:
        # Devrait être très rare
        print(f"Rues les plus proches de {rue} : {res}. Je ne sais que choisir, du coup je reste avec {rue} (normalisé en {étape1}).")
        return étape1
    else:
        # L’adresse fournie n’était sûrement pas un nom de rue.
        print(f"(normalise_rue) Pas de rue connue à moins de {tol} fautes de frappe de {rue} dans la ville {ville}. Je renvoie {étape1}.")
        return étape1
    


    
### Adresses ###

    
class Adresse():
    """
    Attributs
      - num (int)
      - rue (str) : nom de la rue complet
      - rue_norm (str) : nom de rue après normalisation (via normalise_rue)
      - rue_osm (str) : nom de la rue trouvé dans osm (le cas échéant)
      - ville (instance de Ville)
      - pays
    """
    
    def __init__(self, texte, bavard=0):
        """ 
        Entrée : texte d’une adresse. Format : (num)? rue (code_postale? ville)
        """
        e = re.compile("(^[0-9]*)([^()]+)(\((.*)\))?")
        essai = re.findall(e, texte)
        if bavard > 1: print(f"Résultat de la regexp : {essai}")
        if len(essai) == 1:
            num, rue, _, ville = essai[0]
        elif len(essai) == 0:
            raise SyntaxError(f"adresse mal formée : {texte}")
        else:
            print(f"Avertissement : plusieurs interprétations de {texte} : {essai}.")
            num, rue, _, ville = essai[0]
            rue=rue.strip()

        if bavard>0: print(f"analyse de l’adresse : num={num}, rue={rue}, ville={ville}")
        ville_n = normalise_ville(ville)
        rue_n = normalise_rue(rue, ville_n)
        if bavard>0: print(f"arpès normalisation : num={num}, rue_n={rue_n}, ville_n={ville_n}")
        if num=="":
            self.num=None
        else:
            self.num=int(num)
        self.rue=rue
        self.rue_norm = rue_n
        self.rue_osm = None
        self.ville = ville_n
        self.pays=PAYS_DÉFAUT

        
    def __str__(self):
        """
        Utilisé en particulier pour l’enregistrement dans chemins.csv et pour l’affichage pour vérification à l’utilisateur.
        """
        if self.num is not None:
            déb=f"{self.num} "
        else:
            déb=""
        if self.rue_osm is not None:
            return f"{déb}{self.rue_osm} ({self.ville.avec_code()})"
        else:
            return f"{déb}{self.rue} ({self.ville.avec_code()})"

        
    def pour_nominatim(self):
        """
        Renvoie une chaîne de car pour la recherche Nominatim non structurée (si échec de la recherche structurée).
        """
        if self.num is not None:
            déb=f"{self.num} "
        else:
            déb=""
        if self.rue_osm is not None:
            return f"{déb}{self.rue_osm}, {self.ville.avec_code()}, {self.pays}"
        else:
            return f"{déb}{self.rue}, {self.ville.avec_code()}, {self.pays}"


