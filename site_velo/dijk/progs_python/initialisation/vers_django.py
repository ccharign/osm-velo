# -*- coding:utf-8 -*-


##################################################
### Transférer les données dans la base Django ###
##################################################



from dijk.progs_python.params import CHEMIN_NŒUDS_RUES
from dijk.models import Ville, Rue, Sommet, Arête, Nœud_of_Rue, Cache_Adresse, Ville_of_Sommet
from dijk.progs_python.lecture_adresse.normalisation import normalise_ville, normalise_rue, TOUTES_LES_VILLES
from dijk.progs_python.init_graphe import charge_graphe


def nv(nom_ville):
    return normalise_ville(nom_ville).nom_norm

code_postal_norm = {nv(v):code for v,code in TOUTES_LES_VILLES.items()}


def villes_vers_django():
    """
    Effet : réinitialise la table dijk_ville
    """
    Ville.objects.all().delete()
    for nom, code in TOUTES_LES_VILLES.items():
        v = Ville(nom_complet=nom, nom_norm=nv(nom), code=code)
        v.save()

        
def charge_villes_rues_nœuds(g, bavard=0):
    """ 
    Transfert le contenu du csv CHEMIN_NŒUDS_RUES dans la base.
    Réinitialise les tables dijk_rue, dijk_sommet, dijk_ville_of_sommet, dijk_nœud_of_rue
    """

    # Vidage des tables
    Rue.objects.all().delete()
    Sommet.objects.all().delete() # À cause du on_delete=models.CASCADE, ceci devrait vider les autres en même temps
    
    
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
            
            rue_n = normalise_rue(rue, ville)
            rue_d = Rue(nom_complet=rue, nom_norm=rue_n, ville=ville_d, nœuds=nœuds_à_découper)
            rue_d.save()
            
            # nœuds = map(int, nœuds_à_découper.split(","))
            # for n in nœuds:
            #     compte+=1
            #     try:
            #         n_d = Sommet.objects.get(id_osm=n)
            #     except Exception as e :
            #         if bavard >0: print(e)
            #         lat, lon = g.coords_of_nœud(n)
            #         n_d = Sommet(id_osm=n, lon=lon, lat=lat)
            #         n_d.save()
            #     asso = Ville_of_Sommet(sommet=n_d, ville=ville_d)
            #     asso.save()
            #     asso2 = Nœud_of_Rue(ville=ville_d, rue=rue_d, nœud=n_d)
            #     asso2.save()
            #     if bavard>0 and compte%100==0: print(f"{compte} sommets traités.")
            
            
    print("Chargement des rues vers django fini.")

    
        
def transfert(g):
    """
    Entrée : g (graphe)
    Effet : transfert le graphe dans la base Django
    """

    for n in g.digraphe.nodes:
        for m, d in g.voisins(s):
            r = Rue.objects.get(nom_norm = g.digraphe[n][m]["name"])
            # le sommet n
            s = Sommet(id_osm=n, ville=v)
            s.save()
            # l’arête (n,m)
            a = Arête(départ )
            
