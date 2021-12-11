# -*- coding:utf-8 -*-


##################################################
### Transférer les données dans la base Django ###
##################################################



from dijk.progs_python.params import CHEMIN_NŒUDS_RUES
from dijk.models import Ville, Rue, Sommet, Arête, Nœud_of_Rue, Cache_Adresse, Ville_of_Sommet
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

        
def charge_villes_rues_nœuds(bavard=0):
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
            
