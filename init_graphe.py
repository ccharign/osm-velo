# -*- coding:utf-8 -*-

### Fichier destiné à être chargé à chaque utilisation ###


#import networkx as nx

from module_graphe import graphe  # ma classe de graphe
from params import DÉPART

import time
import osmnx.io
import subprocess
import os
#ox.config(use_cache=True, log_console=True)

D_MAX_SUITE_RUE = 10  # Nombre max d’arêtes où on va chercher pour trouver la suite d’une rue.
BBOX = 43.2671, -0.4285, 43.3403, -0.2541 # Convention overpass : sud, ouest, nord, est


# Pour la simplification dans osmnx :
# https://github.com/gboeing/osmnx-examples/blob/master/notebooks/04-simplify-graph-consolidate-nodes.ipynb

# filtrage
# https://stackoverflow.com/questions/63466207/how-to-create-a-filtered-graph-from-an-osm-formatted-xml-file-using-osmnx


#################### Récupération du graphe via osmnx ####################


def charge_graphe_bbox(ouest=-0.4285, sud=43.2671, est=-0.2541, nord=43.3403, option={"network_type":"all"}, bavard=1):
    nom_fichier = f'données/{ouest}{sud}{est}{nord}.graphml'
    try:
        g = osmnx.io.load_graphml(nom_fichier)
        if bavard: print("Graphe en mémoire !")
    except FileNotFoundError:
        subprocess.call([os.path.join(DÉPART, "initialisation/crée_graphe.py"), nom_fichier])
        g = osmnx.io.load_graphml(nom_fichier)

    gr = graphe(g)
    gr.charge_cache()  # nœud_of_rue
    
    print("Chargement de la cyclabilité")
    gr.charge_cycla()
    
    print("Chargement du graphe fini.\n")
    return gr









        
############## Lire tout le graphe pour en extraire les nœuds des rues ###############



def est_sur_rue(g, s, rue):
    """ Indique si le sommet s est sur la rue rue.
    Rappel : il peut y avoir plusieurs rues associées à une arête. rue_dune_arête renvoie un tuple (ou liste)"""
    for t in g.voisins_nus(s):
        rues = g.rue_dune_arête(s,t)
        if rues is not None and rue in rues : return True
    return False


def prochaine_sphère(sph, rue, déjàVu, dmax):
    """ sph est une sphère centrée en s.
        Renvoie les nœuds de rue qui sont sur la première sphère centrée en s qui contienne un nœud de rue. Recherche effectuée en partant de sph et un augmentant le rayon de 1 en 1 au plus dmax fois.
    La distance utilisée est le nombre d’arêtes."""
    if dmax==0:
        return []
    else:
        fini = False
        sph_suivante = []
        for t in sph:
            for u in g.voisins_nus(t):
                if u not in déjàVu:
                    if est_sur_rue(g, u, rue): fini = True
                    sph_suivante.append(u)
                    déjàVu.add(u)
        if not fini:
            return prochaine_sphère(sph_suivante, rue, déjàVu, dmax-1)
        else:
            return ( t for t in sph_suivante if est_sur_rue(g,t,rue) )
                



def extrait_nœuds_des_rues(g, bavard = 0):
    
    déjàVu = {} # dico (nom de rue -> set de nœuds). Ne sert que pour le cas d’une rue qui boucle.
    res = {} # dico (nom de rue -> liste des nœuds dans un ordre topologique )

    
    def suivre_rue(s, sprec, rue):
        """ s (int) : sommet actuel
            sprec (int) : sommet précédent. En entrée de cette fonction, res[rue] doit finir par sprec, s 
            rue (str) : nom de la rue à suivre 
           Effet : remplit déjàVu[rue] ainsi que res[rue]
        """

        # Dans le cas d’une rue qui fourche on aura une branche après l’autre (parcours en profondeur de la rue).
        for t in prochaine_sphère([s], rue, set([s]), D_MAX_SUITE_RUE): # Au cas où la rue serait découpées en plusieurs morceaux dans le graphe. Dans le cas basique, prochaine_sphère renvoie deux sommets, l’un d’eux étant sprec.
            if t != sprec and t not in déjàVu[rue]:
                res[rue].append(t)
                déjàVu[rue].add(t)
                suivre_rue(t,s,rue)

                
    for s in g.digraphe.nodes:
        for t in g.voisins_nus(s):
            rues = g.rue_dune_arête(s,t)
            if rues is not None:
                for rue in rues:
                    if rue not in res:
                        res[rue]=[t, s]
                        déjàVu[rue] = set((s,t))
                        suivre_rue(s, t, rue)
                        res[rue].reverse()
                        suivre_rue(t, s, rue)
                        if bavard: print(f"J’ai suivi la {rue}. Nœuds trouvés : {res[rue]}")
    return res
