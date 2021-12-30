
# -*- coding:utf-8 -*-


##################################################
### Transférer les données dans la base Django ###
##################################################



from dijk.progs_python.params import CHEMIN_NŒUDS_RUES
from dijk.models import Ville, Rue, Sommet, Arête, Cache_Adresse
from dijk.progs_python.lecture_adresse.normalisation import normalise_ville, normalise_rue, TOUTES_LES_VILLES, prétraitement_rue
from dijk.progs_python.init_graphe import charge_graphe


def nv(nom_ville):
    return normalise_ville(nom_ville).nom_norm

code_postal_norm = {nv(v):code for v,code in TOUTES_LES_VILLES.items()}

#Utiliser bulk_create
#https://pmbaumgartner.github.io/blog/the-fastest-way-to-load-data-django-postgresql/

def villes_vers_django():
    """
    Effet : réinitialise la table dijk_ville
    """
    Ville.objects.all().delete()
    villes_à_créer=[]
    for nom, code in TOUTES_LES_VILLES.items():
        villes_à_créer.append( Ville(nom_complet=nom, nom_norm=nv(nom), code=code))
    Ville.objects.bulk_create(villes_à_créer)

        
def charge_rues(bavard=0):
    """ 
    Transfert le contenu du csv CHEMIN_NŒUDS_RUES dans la base.
    Réinitialise la table Rue (dijk_rue)
    """

    # Vidage des tables
    Rue.objects.all().delete()
    #Sommet.objects.all().delete() # À cause du on_delete=models.CASCADE, ceci devrait vider les autres en même temps
    
    rues_à_créer=[]
    with open(CHEMIN_NŒUDS_RUES, "r") as entrée:
        compte=0
        nb_lignes_lues=0
        for ligne in entrée:
            nb_lignes_lues+=1
            if nb_lignes_lues%100==0:
                print(f"ligne {nb_lignes_lues}")
            if bavard>1:print(ligne)
            ville_t, rue, nœuds_à_découper = ligne.strip().split(";")

            ville=normalise_ville(ville_t)
            ville_n = ville.nom_norm
            ville_d = Ville.objects.get(nom_norm=ville_n) # l’objet Django. # get renvoie un seul objet, et filter plusieurs (à confirmer...)
            
            rue_n = prétraitement_rue(rue)
            rue_d = Rue(nom_complet=rue, nom_norm=rue_n, ville=ville_d, nœuds_à_découper=nœuds_à_découper)
            rues_à_créer.append(rue_d)
            
        Rue.objects.bulk_create(rues_à_créer)
            
    print("Chargement des rues vers django fini.")

    
        
def transfert_graphe(g, bavard=0, juste_arêtes=False):
    """
    Entrée : g (graphe_par_networkx)
    Effet : transfert le graphe dans la base Django
    Stratégie pour les arêtes : 
           si entre deux sommets il y a le même nombre d'arêtes avec les mêmes noms, on màj la géométrie (sans doute inutile 99 fois sur 100)
           sinon on efface les anciennes et on remplace par celles de g. Avec la cycla si présente.
    """

    if not juste_arêtes:
        #Chargement des sommets
        à_créer=[]
        à_màj=[]
        nb=0
        for s in g.digraphe.nodes:
            if nb%100==0: print(f"{nb} sommets vus")
            nb+=1
            lon, lat = g.coords_of_nœud(s)
            essai = Sommet.objects.filter(id_osm=s).first()
            if essai is None:
                s_d = Sommet(id_osm=s, lon=lon, lat=lat)
                à_créer.append(s_d)
            else:
                s_d = essai
                #màj des coords au cas où...
                s_d.lon=lon
                s_d.lat=lat
                à_màj.append(s_d)
        Sommet.objects.bulk_create(à_créer)
        Sommet.objects.bulk_update(à_màj, ["lon", "lat"])
            


    # Chargement des arêtes
    def géom_vers_texte(geom):
        """
        Entrée : liste de couples (lon,lat)
        Sortie : str adéquat pour le champ geom d'un objet Arête. 
        """
        coords_texte = (f"{lon},{lat}" for lon, lat in geom)
        return ";".join(coords_texte)
    
    à_créer=[]
    à_màj=[]
    nb=0
    for s in g.digraphe.nodes:
        if nb%100==0:print(f"{nb} arêtes traitées")
        nb+=1
        départ = Sommet.objects.get(id_osm=s)
        for t, arêtes in g.multidigraphe[s].items():
            arrivée = Sommet.objects.get(id_osm=t)

            # Y-a-t-il correspondance exacte entre les anciennes et les nouvelles arêtes ?
            vieilles_arêtes = Arête.objects.filter(départ=départ, arrivée=arrivée)
            noms = [ a.get("name", None) for _, a in arêtes.items()]
            if not any(n is None for n in noms) and len(vieilles_arêtes) == len(arêtes) and all( len(vieilles_arêtes.objects.filter(nom=n)==1 for n in noms )):
                # mode màj. Juste la géom au cas où. 
                for _, a in arêtes.items():
                    a_d = vieilles_arêtes.objects.get(nom=a["name"])
                    a_d.géométrie = géom_vers_texte(a["geometry"].coords)
                    à_màj.append(a_d)
            else:
                # On efface et on recommence
                if len(vieilles_arêtes)>0:
                    LOG(f"Arêtes supprimées : {vieilles_arêtes}.", bavard=2)
                    vieilles_arêtes.delete()
                cycla_dans_g = g.cyclabilité.get((s,t), 1.0)  # Utile juste pour la transition depuis mon vieux graphe qui ne prenait pas en compte les multi-arêtes.
                # En temps normal ce sera 1.0
                for _, a in arêtes.items():
                    nom=a.get("name", None)
                    geom=géom_vers_texte(a["geometry"].coords)
                    a_d = Arête(départ=départ, arrivée=arrivée, longueur=a["length"], cycla=cycla_dans_g, geom =geom)
                    à_créer.append(a_d)
    Arête.objects.bulk_create(à_créer)
    Arête.objects.bulk_update(à_màj, ["geom"])
                 
