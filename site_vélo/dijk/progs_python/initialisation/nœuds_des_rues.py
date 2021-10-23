# -*- coding:utf-8 -*-

############## Lire tout le graphe pour en extraire les nœuds des rues ###############

from params import CHEMIN_NŒUDS_RUES
from lecture_adresse.normalisation import normalise_rue, normalise_ville, prétraitement_rue
D_MAX_SUITE_RUE = 10  # Nombre max d’arêtes où on va chercher pour trouver la suite d’une rue.


def est_sur_rueville(g, s, rue, ville):
    """ Indique si le sommet s est sur la rue et la ville indiquées.
    Rappel : il peut y avoir plusieurs rues et villes associées à une arête. rue_dune_arête et ville_dune_arête renvoient un tuple (ou liste)"""
    for t in g.voisins_nus(s):
        rues = g.rue_dune_arête(s,t)
        villes = g.ville_dune_arête(s,t)
        if rues is not None and rue in rues and ville in villes : return True
    return False


def prochaine_sphère(g, sph, rue, ville, déjàVu, boule, dmax):
    """ sph est une sphère centrée en s.
        boule est la boule fermée correspondante.
        Renvoie les nœuds de rue qui sont sur la première sphère centrée en s qui contienne un nœud de rue. Recherche effectuée en partant de sph et en augmentant le rayon de 1 en 1 au plus dmax fois.
    La distance utilisée est le nombre d’arêtes."""
    if dmax==0:
        return []
    else:
        fini = False
        sph_suivante = []
        res_éventuel = []
        for t in sph:
            for u in g.voisins_nus(t):
                if u not in boule:
                    if est_sur_rueville(g, u, rue, ville) and u not in déjàVu[ville][rue]:
                        fini = True
                        res_éventuel.append(u)
                    sph_suivante.append(u)
                    boule.add(u)
        if not fini:
            return prochaine_sphère(g, sph_suivante, rue, ville, déjàVu, boule, dmax-1)
        else:
            return res_éventuel
                



def extrait_nœuds_des_rues(g, bavard = 0):
    """
    Sortie : dictionnaire ville -> rue -> liste nœuds
    La recherche est faite par des parcours de graphe pour avoir les sommets autant que possible dans l’ordre topologique.
    """
    
    déjàVu = {} # dico (ville -> nom de rue -> set de nœuds). Ne sert que pour le cas d’une rue qui boucle.
    res = {} # dico (ville -> nom de rue -> liste des nœuds dans un ordre topologique )
    
    def suivre_rue(s, ville, rue):
        """ s (int) : sommet actuel
            rue (str) : nom de la rue à suivre 
           Effet : remplit déjàVu[ville][rue] ainsi que res[ville][rue]
        """

        # Dans le cas d’une rue qui fourche on aura une branche après l’autre (parcours en profondeur de la rue).
        for t in prochaine_sphère(g, [s], rue, ville, déjàVu, set([s]), D_MAX_SUITE_RUE): # Au cas où la rue serait découpées en plusieurs morceaux dans le graphe. Dans le cas basique, prochaine_sphère renvoie deux sommets, l’un d’eux étant sprec.
            if t not in déjàVu[ville][rue]:
                res[ville][rue].append(t)
                déjàVu[ville][rue].add(t)
                suivre_rue(t, ville, rue)

    def partir_dune_arête(s,t,ville,rue):
        """ Lance suivre_rue dans le sens (s,t) puis dans le sens (t,s)."""
        suivre_rue(s, rue, ville)
        res[ville][rue].reverse()
        suivre_rue(t, ville, rue)
                
    for s in g.digraphe.nodes:
        for t in g.voisins_nus(s):
            rues = g.rue_dune_arête(s,t)
            villes = g.ville_dune_arête(s,t)
            for ville in villes :
                if ville not in déjàVu:
                    print(f"Nouvelle ville rencontrée : {ville}")
                    déjàVu[ville] = {}
                    res[ville] = {}
                if rues is not None:
                    for rue in rues:
                        if rue not in res[ville]:
                            res[ville][rue] = [t, s]
                            déjàVu[ville][rue] = set((s,t))
                            partir_dune_arête(s,t,ville,rue)
                        if s not in déjàVu[ville][rue] or t not in déjàVu[ville][rue]:  # Cas d’un nouveau tronçon d’une ancienne rue
                            partir_dune_arête(s,t,ville,rue)
                            
                            if bavard>1: print(f"J’ai suivi la {rue} à {ville}. Nœuds trouvés : {res[ville][rue]}")
    return res


def sortie_csv(g, bavard=0):
    """ 
    Met le dictionnaire ville -> rue -> nœuds dans le csv situé à CHEMIN_NŒUDS_RUES
    Structure d’une ligne : ville;rue;nœuds séparés par virgule.
    """
    res = extrait_nœuds_des_rues(g, bavard=bavard)
    print(f"Enregistrement des nœuds des rues dans {CHEMIN_RUE_NUM_COORDS}")
    with open(CHEMIN_NŒUDS_RUES, "w") as sortie:
        for ville, d in res.items():
            for rue, nœuds in d.items():
                ligne = f"{ville};{rue};{','.join(map(str,nœuds))}\n"
                sortie.write(ligne)

                
def charge_csv(g):
    """ Charge le dictionnaire depuis le csv et le met dans l’attribut nœuds du graphe g.
    Les clefs (ville et rue) sont traitées via les fonctions de normalisation de lecture_adresse.normalisation.
    """
    with open(CHEMIN_NŒUDS_RUES, "r") as entrée:
        for ligne in entrée:
            ville, rue, nœuds_à_découper = ligne.strip().split(";")
            ville = normalise_ville(ville)
            ville_n=ville.nom_norm
            rue = prétraitement_rue(rue) # Il ne devrait pas y avoir de faute de frappe dans le csv : je saute la recherche dans l’arbre lex.
            nœuds = list(map(int, nœuds_à_découper.split(",")))
            if ville_n not in g.nœuds : g.nœuds[ville_n]={}
            g.nœuds[ville_n][rue] = nœuds
    print("Chargement de la liste des nœuds de chaque rue finie.")
            
