# -*- coding:utf-8 -*-

#import networkx as nx

from module_graphe import graphe  # ma classe de graphe
import xml.etree.ElementTree as xml  # Manipuler le xml local
from params import CHEMIN_XML, CHEMIN_XML_COMPLET, CHEMIN_JSON_NUM_COORDS, CHEMIN_NŒUDS_VILLES  # Chemin du xml élagué
import re
import time
import osmnx.io
from récup_données import recherche_inversée
import subprocess
import overpy
from petites_fonctions import ajouteDico
#ox.config(use_cache=True, log_console=True)

D_MAX_SUITE_RUE = 10  # Nombre max d’arêtes où on va chercher pour trouver la suite d’une rue.
BBOX = -0.4285, 43.2671,-0.2541,43.3403

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
        subprocess.call(["crée_graphe.py", nom_fichier])
        g = osmnx.io.load_graphml(nom_fichier)

    gr = graphe(g)
    gr.charge_cache()  # nœud_of_rue
    print("Chargement de la cyclabilité")
    gr.charge_cycla()
    print("Chargement du graphe fini.\n")
    return gr



#################### Élaguage ####################


def élague_xml(chemin="données_inutiles/pau_agglo.osm"):
    """
    Entrée : chemin, chemin vers un fichier .osm
             chemin_sortie, autre chemin
    Effet : enregistre dans CHEMIN_XML (défini dans params.py) un .osm contenant uniquement les voies, leur id, leur nom et les ref des nœuds qui la composent du .osm initial.
    """

    print(f"Chargement du xml {chemin}")
    a = xml.parse(chemin).getroot()
    print("Création de l'arbre simplifié")
    res = xml.Element("osm")
    for c in a:
        if c.tag == "way":
            fils = xml.SubElement(res, "way")
            fils.attrib["id"] = c.attrib["id"]
            
            for d in c:
                if d.tag == "nd":  # Les nœuds osm sur le way c
                    petit_fils = xml.SubElement(fils, "nd")
                    petit_fils.attrib["ref"] = d.attrib["ref"]
                elif d.tag == "tag" and d.attrib["k"] == "name":  # le nom de c
                    petit_fils = xml.SubElement(fils, "tag")
                    petit_fils.attrib["k"] = "name"
                    petit_fils.attrib["v"] = d.attrib["v"]
    print("Enregistrement du xml simplifié")
    xml.ElementTree(res).write(CHEMIN_XML, encoding="utf-8")



    
#################### Récupération des numéros de rues ####################
    

def coords_of_nœud_xml(c):
    return float(c.attrib["lat"]), float(c.attrib["lon"])


def int_of_num(n, bavard=0):
    """ Entrée : une chaîne représentant un numéro de rue.
        Sortie : ce numéro sous forme d’entier. Un éventuel "bis" ou "ter" sera supprimé."""
    e = re.compile("\ *([0-9]*)[^0-9]*$")
    if bavard: print(n, re.findall(e, n))
    num = re.findall(e, n)[0]
    return int(num)


def normalise_ville(ville):
    """En minuscule avec capitale majuscule."""
    return ville.title()


def commune_of_adresse(adr):
    """ Entrée : adresse renvoyée par Nominatim.reverse.
        Sortie : la commune (on espère)"""
    à_essayer = ["city", "village", "town"]
    for clef in à_essayer:
        try:
            return adr[clef]
        except KeyError :
            pass



def extrait_rue_num_coords(chemin="données_inutiles/pau.osm", bavard=0):
    """ Entrée : fichier xml d’openstreetmap (pas la version élaguée)
        Effet : crée un fichier texte associant à chaque rue la list des (numéro connu, coords correspondantes)"""
    

    print("Chargement du xml")
    a = xml.parse("données_inutiles/pau.osm").getroot()
    
    print("Extraction des adresses connues")
    
    def ajoute_dans_res(villerue, val):
        if villerue not in res:
            res[villerue] = []
        res[villerue].append(val)
        
    res = {}
    nums_seuls = []
    for c in a:
        if c.tag == "node":  # Sinon on n’a pas les coords.
            # Voyons si nous disposons d’une adresse pour ce nœud.
            num, rue, ville = None, None, None
            for d in c:
                if d.tag == "tag" and d.attrib["k"] == "addr:housenumber":
                    num = d.attrib["v"]
                if d.tag == "tag" and d.attrib["k"] == "addr:street":
                    rue = d.attrib["v"]
                if d.tag == "tag" and d.attrib["k"] == "addr:city":
                    ville = normalise_ville(d.attrib["v"])
            if num is not None:
                try:
                    num = int_of_num(num)
                    if rue is not None and num is not None and ville is not None:
                        ajoute_dans_res(ville+";"+rue, (num, float(c.attrib["lat"]), float(c.attrib["lon"])))
                    else:
                        # juste un numéro
                        nums_seuls.append( (c.attrib["id"], num, float(c.attrib["lat"]), float(c.attrib["lon"])) )
                except Exception as e:  # pb dans le xml
                    print(f"Pb à  la lecture du nœud {num, rue, ville}  : {e}.\n Nœud abandonné.")
            


    print("Recherche des rues des numéros orphelins")
    print("Recherche inversée Nominatim limitée à une recherche par seconde...")
    nb=0
    for id_node, num, lat, lon in nums_seuls:
        try:
            adresse = recherche_inversée((lat, lon)).raw["address"]
            if bavard>0: print(adresse)
            villerue = commune_of_adresse(adresse) + ";"+adresse["road"]
            ajoute_dans_res(villerue, (num, lat, lon))
            nb+=1
        except Exception as e:
            print(f"Erreur pour {id_node, num, lat, lon} : {e}")
    print(f"{nb} adresses collectées")
        
    print("Écriture du fichier")
    sortie = open(CHEMIN_JSON_NUM_COORDS, "w")
    for villerue, l in res.items():
        if len(l) > 1:  # Une seule adresse dans la rue ça ne permet pas d’interpoler.
            l_pair = [x for x in l if x[0]%2 == 0]
            l_impair = [x for x in l if x[0]%2 != 0]
            
            def à_écrire(ll):
                ll.sort()
                ll = [ x for i,x in enumerate(ll) if i==0 or x[0]!=ll[i-1][0] ]  # dédoublonnage des numéros
                if bavard: print(à_écrire)
                return "|".join([str(c)[1:-1] for c in ll])
                
            sortie.write(f"{villerue}:{';'.join([à_écrire(l_pair), à_écrire(l_impair)])}\n")
    sortie.close()
    #return nums_seuls



#################### Rajouter la ville aux données des nœuds ####################


def liste_villes():
    """ Liste des villes apparaissant dans CHEMIN_JSON_NUM_COORDS."""
    res = set([])
    with open(CHEMIN_JSON_NUM_COORDS) as f:
        for ligne in f:
            res.add(ligne.split(";")[0])
    return res


api = overpy.Overpass()
def nœuds_ville(ville):
    r = api.query(f"""
    area["name"="{ville}"]
        ["boundary"="administrative"]
        {BBOX}->.a;
    node(area.a);
    out;
    """)
    return r.nodes



def ajoute_villes(g):
    """ Ajoute un champ "ville" à chaque arête de g qui contient une liste de villes. Sauvegarde de plus les nœuds de g de chaque ville dans un csv."""
    sortie = open(CHEMIN_NŒUDS_VILLES,"w")
    for ville in liste_villes():
        l = []
        nœuds = nœuds_ville(ville)
        for n in nœuds:
            if n in g.digraphe.nodes:
                l.append(n) # Pour le csv
                # Remplissage du graphe
                for v in g.voisins_nus(n):
                    if v in nœuds:
                        ajouteDico( g.digraphe[n][v], "ville", ville )
                        ajouteDico( g.digraphe[v][n], "ville", ville )
        ligne = ville + ";" + ",".join(map(str,l))
        sortie.write(ligne+"\n")



        
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
