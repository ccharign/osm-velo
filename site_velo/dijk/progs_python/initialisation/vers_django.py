
# -*- coding:utf-8 -*-


##################################################
### Transférer les données dans la base Django ###
##################################################



from dijk.progs_python.params import CHEMIN_NŒUDS_RUES
from dijk.models import Ville, Rue, Sommet, Arête, Cache_Adresse, Chemin_d, Ville_Zone
from dijk.progs_python.lecture_adresse.normalisation import normalise_ville, normalise_rue, prétraitement_rue, partie_commune
#from dijk.progs_python.init_graphe import charge_graphe
from params import CHEMIN_CHEMINS, LOG
from petites_fonctions import union, mesure_temps
from time import perf_counter, sleep
from django.db import transaction
from lecture_adresse.arbresLex import ArbreLex


# L’arbre contient les f"{nom_norm}|{code}"
def à_mettre_dans_arbre(nom_n, code):
    return f"{nom_n}|{code}"


def arbre_des_villes(zone_d=None):
    """
    Renvoie l’arbre lexicographique des villes de la base.
    Si zone_d est précisé, seulement les villes de cette zone.
    """
    res = ArbreLex()
    if zone_d is None:
        villes = Ville.objects.all()
    else:
        villes = zone_d.villes()
    for v_d in villes:
        res.insère(à_mettre_dans_arbre(v_d.nom_norm, v_d.code))
    return res


def nv_ville(nom, code, zone_d, tol=3):
    """
    Effet : si pas déjà présente, rajoute la ville dans la base django et dans l'arbre lex ARBRE_VILLES.
    Sortie : l'objet Ville créé ou récupéré dans la base.
    """
    nom_norm = partie_commune(nom)
    arbre = arbre_des_villes()
    dans_arbre, d = arbre.mots_les_plus_proches(à_mettre_dans_arbre(nom_norm, code), d_max=tol)
    
    if len(dans_arbre) > 0:
        print(f"Ville(s) trouvée(s) dans l'arbre : {tuple(dans_arbre)}")
        nom_n_corrigé, code_corrigé = tuple(dans_arbre)[0].split("|")
        if d>0:
            LOG(f"Avertissement : la ville {nom_norm, code} a été corrigée en {nom_n_corrigé, code_corrigé}")
        v_d = Ville.objects.get(nom_norm=nom_n_corrigé, code=code_corrigé)
        return v_d
    
    else:
        v_d = Ville(nom_complet=nom, code=code, nom_norm=nom_norm)
        v_d.save()
        rel = Ville_Zone(ville=v_d, zone=zone_d)
        rel.save()
        return v_d

    
def liste_attributs(g):
    """
    Entrée : g (multidigraph)
    Sortie : dico (attribut -> liste des valeurs) des arêtes qui apparaissent dans g
    Fonction utile pour régler les paramètres de cycla_défaut.
    """

    res = {}
    for s in g.nodes:
        for t in g[s].keys():
            for a in g[s][t].values():
                for att, val in a.items():
                    if att not in ["name", "length", "geometry", "osmid"]:
                        if att not in res:res[att]=set()
                        res[att].add(str(val))
    return res


def désoriente(g, bavard=0):
    """
    Entrée : g (Graphe_nx)
    Effet : rajoute les arêtes inverses si elles ne sont pas présentes, avec un attribut 'sens_interdit' en plus.
    """
    
    def existe_inverse(s,t,a):
        if s not in gx[t]:
            return False
        else:
            inverses_de_a = tuple(a_i for a_i in gx[t][s].values() if a.get("name",None)==a_i.get("name", None))
            if len(inverses_de_a)==1:
                return True
            elif len(inverses_de_a)==0:
                return False
            else:
                inverses_de_a = tuple(a_i for a_i in inverses_de_a if sorted(géom_texte(s,t,a,g) )==sorted(géom_texte(t,s,a_i,g)))
                if len(inverses_de_a)==1:
                    return True
                elif len(inverses_de_a) == 0:
                    return False
                else:
                    raise RuntimeError(f"Arête en double : {s}, {t}, {a}")
                
    def ajoute_inverse(s,t,a):
        if bavard>0:
            print(f"ajout de l’arête inverse de {s}, {t}, {a}")
        a_i = {att:val for att,val in a.items()}
        a_i["sens_interdit"]=True
        gx.add_edge(t,s,**a_i )
        # 
        # if s not in gx[t]:
        #     gx[t][s] = {0:a_i}
        # else:
        #     ind = max(gx[t][s].keys())
        #     gx[t][s] [ind+1] = a_i

        
    gx=g.multidigraphe
    for s in gx.nodes:
        for t in gx[s].keys():
            if t!=s:  # Il semble qu’il y ait des doublons dans les boucles dans les graphes venant de osmnx
                for a in gx[s][t].values():
                    if not existe_inverse(s, t, a):
                        ajoute_inverse(s,t,a)
                    
@transaction.atomic
def sauv_données(à_sauver):
    """
    Sauvegarde les objets en une seule transaction.
    Pour remplacer bulk_create si besoin du champ id nouvellement créé.
    """
    for o in à_sauver:
        try:
            o.save()
        except Exception as e:
            print(f"Problème pour enregistrer {o} : {e}.")

def géom_texte(s, t, a, g):
    """
    Entrée : a (dico), arête de nx.
             s_d, t_d (Sommet, Sommet), sommets de départ et d’arrivée de a
    Sortie : str adéquat pour le champ geom d'un objet Arête. 
    """
    if "geometry" in a:
        geom = a["geometry"].coords
    else:
        geom = (g.coords_of_nœud(s), g.coords_of_nœud(t))
    coords_texte = (f"{lon},{lat}" for lon, lat in geom)
    return ";".join(coords_texte)



def cycla_défaut(a, sens_interdit=False, pas=1.1):
    """
    Entrée : a, arête d'un graphe nx.
    Sortie (float) : cycla_défaut
    Paramètres:
        pas : pour chaque point de bonus, on multiplie la cycla par pas
        sens_interdit : si Vrai, bonus de -2
    Les critères pour attribuer des bonus en fonction des données osm sont définis à l’intérieur de cette fonction.
    """
    # disponible dans le graphe venant de osmnx :
    # maxspeed, highway, lanes, oneway, access, width
    critères={
        #att : {val: bonus}
        "highway":{
            "residential":1,
            "cycleway":3,
            "step":-3,
            "pedestrian":1,
            "tertiary":1,
            "living_street":1,
            "pedestrian":1,
            "footway":1,
        },
        "maxspeed":{
            "10":3,
            "20":2,
            "30":1,
            "70":-2,
            "90":-4,
            "130":-float("inf")
        },
        "sens_interdit":{True:-3}
    }
    bonus = 0
    for att in critères.keys():
        if att in a:
            val_s = a[att]
            if isinstance(val_s, str) and val_s in critères[att]:
                bonus+=critères[att][val_s]
            elif isinstance(val_s, list):
                for v in val_s:
                    if v in critères[att]:
                        bonus+= critères[att][v]

    return 1.1**bonus


def transfert_graphe(g, zone_d, bavard=0, rapide=1, juste_arêtes=False):
    """
    Entrée : g (Graphe_nx)
             zone_d (instance de Zone)
    Effet : transfert le graphe dans la base Django.
    Paramètres:
        rapide (int) : pour tout  (s,t) sommets voisins dans g,
                            0 -> efface toutes les arêtes de s vers t et remplace par celles de g
                            1 -> regarde si les arête entre s et t dans g correspondent à celles dans la base, et dans ce cas ne rien faire.
                        « correspondent » signifie : même nombre et même noms.
                            2 -> si il y a quelque chose dans la base pour (s,t), ne rien faire.
        juste_arêtes (bool) : si vrai, ne recharge pas les sommets.
    """

    gx = g.multidigraphe

    ### Chargement des arêtes###

    tous_les_sommets = Sommet.objects.all()
    print(f"{len(tous_les_sommets)} sommets dans la base")

    dico_voisins={}
    toutes_les_arêtes = Arête.objects.all().select_related("départ", "arrivée")
    for a in toutes_les_arêtes:
        s = a.départ.id_osm
        t = a.arrivée.id_osm
        if s not in dico_voisins: dico_voisins[s]=[]
        dico_voisins[s].append((t, a))

        
    if not juste_arêtes:
        LOG("Chargement des sommets")
        à_créer=set()
        à_màj=[]
        nb=0
        for s in g.digraphe.nodes:
            if nb%100==0: print(f"    {nb} sommets vus")
            nb+=1
            lon, lat = g.coords_of_nœud(s)
            essai = Sommet.objects.filter(id_osm=s).first()
            if essai is None:
                s_d = Sommet(id_osm=s, lon=lon, lat=lat)
                à_créer.add(s_d)
            else:
                s_d = essai
                #màj des coords au cas où...
                s_d.lon=lon
                s_d.lat=lat
                à_màj.append(s_d)
        LOG(f"Ajout des {len(à_créer)} nouveaux sommets dans la base")
        #créés=Sommet.objects.bulk_create(à_créer) # Attention : les objets renvoyés par bulk_create n’ont pas d’id
        sauv_données(à_créer)
        #if len(créés) != len(à_créer):
        #    raise RuntimeError(f"{len(créés)} sommets créés par bulk_create alors qu’il fallait en créer {len(à_créer)}")
        LOG(f"Mise à jour des {len(à_màj)} sommets modifiés")
        Sommet.objects.bulk_update(à_màj, ["lon", "lat"])

        LOG("Ajout de la zone à chaque sommet")
        # Pas possible avant car il faut avoir sauvé l’objet pour rajouter une relation ManyToMany.
        # Il faudrait un bulk_manyToMany ... -> utiliser la table d’association automatiquement créée par Django : through
        #https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField
        print("Sommets créés")
        rel_àcréer=[]
        for s_d in à_créer:
            rel = Sommet.zone.through(sommet_id = s_d.id, zone_id = zone_d.id)
            rel_àcréer.append(rel)
        print("Sommets mis à jour")
        for s_d in à_màj:
            if zone_d not in s_d.zone.all() :
                rel = Sommet.zone.through(sommet_id = s_d.id, zone_id = zone_d.id)
                rel_àcréer.append(rel)
        Sommet.zone.through.objects.bulk_create(rel_àcréer)


    ### Transfert des arêtes ###

    # pour profiling
    temps={"correspondance":0., "remplace_arêtes":0., "màj_arêtes":0., "récup_nom":0.}
    nb_appels={"correspondance":0, "remplace_arêtes":0, "màj_arêtes":0, "récup_nom":0}
    
    
    #@mesure_temps("récup_nom", temps, nb_appels)
    def récup_noms(arêtes_d, nom):
        """ Renvoie le tuple des a∈arêtes_d qui ont pour nom 'nom'"""
        return [a_d for a_d in arêtes_d if nom==a_d.nom]
    
    #@mesure_temps("correspondance", temps, nb_appels)
    def correspondance(s_d, t_d, s, t, gx):
        """
        Entrées:
            - s_d, t_d (Sommet)
            - s, t (int)
            - gx (multidigraph)
        Sortie ( bool × (Arête list) × (dico list)) : le triplet ( les arêtes correspondent à celles dans la base, arêtes de la bases, arêtes de gx)
        Dans le cas où il y a correspondance, les deux listes renvoyées contiennent les arêtes dans le même ordre.
        Ne prend en compte que les arêtes de s_d vers t_d.
        « Correspondent » signifie ici même nombre, et mêmes noms. En cas de plusieurs arêtes de même nom, le résultat sera Faux dans tous les cas.
        """
        vieilles_arêtes = [a_d for (v, a_d) in dico_voisins.get(s, []) if v==t]
        if t not in gx[s]:
            return False, vieilles_arêtes, []
        else:
            arêtes = gx[s][t].values()
            noms = [ a.get("name", None) for a in arêtes ]
            if len(noms)!= len(vieilles_arêtes):
                return False, vieilles_arêtes, arêtes
            else:
                arêtes_ordre = []
                for a in arêtes:
                    essai_a_d = récup_noms(vieilles_arêtes, a.get("name", None) )
                    if len(essai_a_d) != 1:
                        #if vieilles_arêtes.filter(nom=a.get("name", None)).count()!=1:
                        return False, vieilles_arêtes, arêtes
                    else:
                        arêtes_ordre.append(essai_a_d[0])
                    
                return True, arêtes_ordre, arêtes

    à_créer=[]
    à_màj=[]
    
    #@mesure_temps("màj_arêtes", temps, nb_appels)
    def màj_arêtes(s_d, t_d, s, t, arêtes_d, arêtes_x):
        """
        Entrées:
            - arêtes_d (Arête list) : arêtes de la base
            - arêtes_x (dico list) : arêtes de gx
        Précondition : les deux listes représentent les mêmes arêtes, et dans le même ordre
        Effet:
            Met à jour les champs cycla_défaut, zone, géométrie des arêtes_d avec les données des arête_nx.
            Rajoute les arêtes dans à_màj : il faudra encore un Arête.bulk_update(à_maj).
        """
        for a_d, a_x in zip(arêtes_d, arêtes_x):
            #a_d.geom = géom_texte(s, t, a_x, g)
            #a_d.zone.add(zone_d)
            a_d.cycla_défaut= cycla_défaut(a_x)
            à_màj.append(a_d)


    #@mesure_temps("remplace_arêtes", temps, nb_appels)
    def remplace_arêtes(s_d, t_d, s, t, arêtes_d, gx):
        """
        Supprime les arêtes de arêtes_d, et crée à la place celles venant de arêtes_nx.
        Sortie (Arête list): les arêtes créées.
        """
        #arêtes_d.delete()
        for a in arêtes_d: a.delete()
        if t in gx[s]:
            arêtes_nx = gx[s][t].values()
        else:
            arêtes_nx=[]
        res=[]
        for a_nx in arêtes_nx:
            a_d = Arête(départ=s_d, arrivée=t_d,
                        nom=a_nx.get("name", None),
                        longueur=round(a_nx["length"], 3),  # On enregistre les longueurs avec 3 décimales.
                        cycla_défaut=cycla_défaut(a_nx),
                        geom =géom_texte(s, t, a_nx, g)
            )
            res.append(a_d)
        à_créer.extend(res)
        return res

    LOG("Chargement des arêtes depuis le graphe osmnx")
    nb=0
    
    for s in gx.nodes:
        s_d = tous_les_sommets.get(id_osm=s)
        for t, arêtes in gx[s].items():
            if t!=s : # Suppression des boucles
                nb+=1
                if nb%500==0:print(f"    {nb} arêtes traitées\n ") #{temps}\n{nb_appels}\n")
                t_d = tous_les_sommets.get(id_osm=t)
                correspondent, arêtes_d, arêtes_x =  correspondance(s_d, t_d, s, t, gx)
                if not (rapide==2 and len(arêtes_d)>0):
                    if rapide==0 or not correspondent:
                        arêtes_d=remplace_arêtes(s_d, t_d, s, t, arêtes_d, gx)
                    else:
                        màj_arêtes(s_d, t_d, s, t, arêtes_d, arêtes_x)
    
    LOG("Ajout des nouvelles arêtes dans la base")
    #créées=Arête.objects.bulk_create(à_créer)
    sauv_données(à_créer)
    #print(f"{len(créées)} arêtes créées")
    #if len(créées)!=len(à_créer):
    #    raise RuntimeError(f"Pas le bon nombre d’arêtes créées.")
    LOG("Mise à jour des anciennes arêtes")
    Arête.objects.bulk_update(à_màj, ["cycla_défaut"])

    LOG("Ajout de la zone à chaque arête")
    nb=0
    rel_àcréer=[]
    for i, a_d in enumerate(à_créer):
        rel = Arête.zone.through(arête_id = a_d.id, zone_id = zone_d.id)
        rel_àcréer.append(rel)
    Arête.zone.through.objects.bulk_create(rel_àcréer)
    rel_àcréer=[]
    for a_d in à_màj:
        if zone_d not in a_d.zone.all() :
            rel = Arête.zone.through(arête_id = a_d.id, zone_id = zone_d.id)
            rel_àcréer.append(rel)
        nb+=1
        if nb%1000==0:print(f"    {nb} arêtes traités")
    Arête.zone.through.objects.bulk_create(rel_àcréer)


@transaction.atomic()
def charge_dico_rues_nœuds(ville_d, dico):
    """
    Entrée :
        - ville_d (instance de ville)
        - dico : un dico nom_de_rue -> liste de nœuds
    Effet :
        remplit la table dijk_rue. Si une rue était déjà présente, elle sera supprimée.
    """
    rues_à_créer=[]
    for rue_n, nœuds in dico.items():
        #rue_n = prétraitement_rue(rue)
        assert rue_n == prétraitement_rue(rue_n), f"La rue suivante n’était pas normalisée : {rue_n}"
        nœuds_texte = ",".join(map(str, nœuds))
        vieilles_rues = Rue.objects.filter(nom_norm=rue_n, ville=ville_d)
        vieilles_rues.delete()
        rue_d = Rue(nom_complet=rue_n, nom_norm=rue_n, ville=ville_d, nœuds_à_découper=nœuds_texte)
        rues_à_créer.append(rue_d)
    Rue.objects.bulk_create(rues_à_créer)
        

### vieux trucs ###



def nv(g, nom_ville):
    return normalise_ville(g, nom_ville).nom_norm

#code_postal_norm = {nv(v):code for v,code in TOUTES_LES_VILLES.items()}

#Utiliser bulk_create
#https://pmbaumgartner.github.io/blog/the-fastest-way-to-load-data-django-postgresql/

def villes_vers_django(g):
    """
    Effet : réinitialise la table dijk_ville
    """
    Ville.objects.all().delete()
    villes_à_créer=[]
    for nom, code in TOUTES_LES_VILLES.items():
        villes_à_créer.append( Ville(nom_complet=nom, nom_norm=nv(g, nom), code=code))
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


@transaction.atomic
def charge_csv_chemins(réinit=False):
    """
    Effet : charge le csv de CHEMIN_CHEMINS dans la base
    Si réinit, vide au prélable la table.
    """
    if réinit:
        Chemin_d.objects.all().delete()
    with open(CHEMIN_CHEMINS) as entrée:
        à_créer=[]
        for ligne in entrée:
            print(ligne)
            AR_t, pourcentage_détour_t, étapes_t,rues_interdites_t = ligne.strip().split("|")
            p_détour = int(pourcentage_détour_t)/100.
            if AR_t=="True": AR=True
            else: AR=False
            début, fin = étapes_t[:255], étapes_t[-255:]
            interdites_début, interdites_fin = rues_interdites_t[:255], rues_interdites_t[-255:]
            c_d = Chemin_d(ar=AR, p_détour=p_détour, étapes_texte=étapes_t, interdites_texte=rues_interdites_t, début=début, fin = fin, interdites_début=interdites_début, interdites_fin=interdites_fin)
            c_d.sauv()
