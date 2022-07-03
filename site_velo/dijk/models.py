import json

from django.db import models
from dijk.progs_python.params import CHEMIN_CHEMINS, LOG
from dijk.progs_python.lecture_adresse.normalisation0 import partie_commune, prétraitement_rue
#from dijk.progs_python.lecture_adresse.normalisation import normalise_rue
from dijk.progs_python.recup_donnees import rue_of_coords

# Create your models here.


def découpe_chaîne_de_nœuds(c):
    return tuple(map(int, c.split(",")))


class Ville(models.Model):
    nom_complet = models.CharField(max_length=100)
    nom_norm = models.CharField(max_length=100)
    code = models.IntegerField(null=True)
    code_insee = models.IntegerField(null=True, default=None, blank=True)
    population = models.IntegerField(null=True, default=None, blank=True)
    densité = models.SmallIntegerField(null=True, default=None, blank=True)
    géom_texte = models.TextField(null=True, default=None, blank=True)
    données_présentes = models.BooleanField(default=False)
    #zone = models.ManyToManyField(Zone) # pb car la classe Zone n’est pas encore définie.

    def __str__(self):
        return self.nom_complet

    def avec_code(self):
        return f"{self.code} {self.nom_complet}"

    def voisine(self):
        rels = Ville_Ville.objects.filter(ville1=self).select_related("ville2")
        return tuple(r.ville2 for r in rels)

    @classmethod
    def of_nom(cls, nom):
        """ Renvoie la ville telle que partie_commune(nom) = ville.nom_norm"""
        return cls.objects.get(nom_norm=partie_commune(nom))
    
    
class Ville_Ville(models.Model):
    """ table d’association pour indiquer les villes voisines."""
    ville1 = models.ForeignKey(Ville, related_name="ville1", on_delete=models.CASCADE)
    ville2 = models.ForeignKey(Ville, related_name="ville2", on_delete=models.CASCADE)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=["ville1", "ville2"], name = "Pas de relation ville_ville en double."),
        ]

        
class Zone(models.Model):
    """
    Une zone délimite une zone dont le graphe sera mis en mémoire au chargement.
    """
    nom = models.CharField(max_length=100, unique=True)
    ville_défaut = models.ForeignKey(Ville, on_delete=models.CASCADE)
    
    def villes(self):
        return (rel.ville for rel in Ville_Zone.objects.filter(zone=self).prefetch_related("ville"))
    
    def __str__(self):
        return self.nom
    
    def __hash__(self):
        return self.pk


class Ville_Zone(models.Model):
    """
    Table d’association
    """
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=["zone", "ville"], name = "Pas de relation en double.")
        ]


class Sommet(models.Model):
    
    id_osm = models.BigIntegerField(unique=True)
    lon = models.FloatField()
    lat = models.FloatField()
    zone = models.ManyToManyField(Zone)
    
    def __str__(self):
        return str(self.id_osm)

    # Sert dans les tas de Dijkstra au cas où deux sommets aient exactement la même distance au départ
    def __lt__(self, autre):
        return self.id_osm < autre

    def __hash__(self):
        return self.id_osm

    def voisins(self, p_détour):
        arêtes = Arête.objects.filter(départ=self).select_related("arrivée")
        return [(a.arrivée, a.longueur_corrigée(p_détour)) for a in arêtes]

    def voisins_nus(self):
        arêtes = Arête.objects.filter(départ=self).select_related("arrivée")
        return [a.arrivée for a in arêtes]

    def coords(self):
        return self.lon, self.lat

    def prédécesseurs(self):
        arêtes = Arête.objects.filter(arrivée=self).select_related("départ")
        return [a.départ for a in arêtes]


# https://docs.djangoproject.com/en/3.2/topics/db/examples/many_to_many/
class Rue(models.Model):
    """
    Une entrée pour chaque couple (rue, ville) : certaines rues peuvent apparaître en double.
    """
    nom_complet = models.CharField(max_length=200)
    nom_norm = models.CharField(max_length=200)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    nœuds_à_découper = models.TextField()  # chaîne de caractères contenant les nœuds à splitter

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["nom_norm", "ville"], name="une seule rue pour chaque nom_norm pour chaque ville.")
        ]
    
    def __str__(self):
        return f"{self.nom_complet}"
    
    def nœuds(self):
        return découpe_chaîne_de_nœuds(self.nœuds_à_découper)



def formule_pour_correction_longueur(l, cy, p_détour):
    """
    Ceci peut être changé. Actuellement : l / cy**( p_détour*1.5)
    Rappel : cy>1 == bien
             cy<1 == pas bien
    """
    return l / cy**(p_détour*1.5)


class Arête(models.Model):
    """
    Attributs:
        départ (Sommet)
        arrivée (Sommet)
        longueur (float)
        cycla (float) : cyclabilité calculée par l'IA. None par défaut.
        cycla_défaut (float) : cyclabilité obtenue par les données présentes dans osm. Via la fonction vers_django.cycla_défaut lors du remplissage de la base.
        rue (Rue). Ce champ est-il utile ?
        geom (string). Couples lon,lat séparés par des ;
        nom (str)
        zone (Zone ManyToMany)
        sensInterdit (BooleanField)
    """
    départ = models.ForeignKey(Sommet, related_name="sommet_départ", on_delete=models.CASCADE, db_index=True)
    arrivée = models.ForeignKey(Sommet, related_name="sommet_arrivée", on_delete=models.CASCADE)
    longueur = models.FloatField()
    cycla = models.FloatField(blank=True, null=True, default=None)
    cycla_défaut = models.FloatField(default=1.0)
    rue = models.ManyToManyField(Rue)
    geom = models.TextField()
    nom = models.CharField(max_length=200, blank=True, null=True, default=None)
    zone = models.ManyToManyField(Zone)
    sensInterdit = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id} : ({self.départ}, {self.arrivée}, longueur : {self.longueur}, géom : {self.geom}, nom : {self.nom})"

    # Sert dans meilleure_arête en cas d’égalité des longueurs
    def __lt__(self, autre):
        return self.id < autre
    def __gt__(self, autre):
        return self.id > autre
    

    def géométrie(self):
        """
        Sortie ( float*float list ) : liste de (lon, lat) qui décrit la géométrie de l'arête.
        """
        res=[]
        for c in self.geom.split(";"):
            lon, lat = c.split(",")
            res.append((float(lon), float(lat)))
        return res

    def cyclabilité(self):
        if self.cycla is not None:
            return self.cycla
        else:
            return self.cycla_défaut

    def incr_cyclabilité(self, dc):
        assert dc > 0, f"j’ai reçu dc={dc}."
        if self.cycla is not None:
            self.cycla *= dc
        else:
            self.cycla = self.cycla_défaut * dc
        self.save()
    
    def longueur_corrigée(self, p_détour):
        """
        Entrée : p_détour (float), proportion de détour.
        Sortie : Longueur corrigée par la cyclabilité.
        """
        cy = self.cyclabilité()
        assert cy > 0, f"cyclabilité ⩽ pour l’arête {self}. Valeur : {cy}."
        return formule_pour_correction_longueur(self.longueur, cy, p_détour)



class Chemin_d(models.Model):
    """
    Attributs:
        - ar (bool)
        - p_détour (float) proportion détour
        - étapes_texte (str)
        - interdites (str)
        - utilisateur (str)
        - date (DateField) : date de création
        - dernier_p_modif (float) : nb d’arêtes modifiées / distance entre départ et arrivée lors du dernier apprentissage.
        - zone (Zone)
    """
    ar=models.BooleanField(default=False)
    p_détour=models.FloatField()
    étapes_texte=models.TextField()
    interdites_texte=models.TextField(default=None, blank=True, null=True)
    utilisateur = models.CharField(max_length=100, default=None, blank=True, null=True)
    dernier_p_modif = models.FloatField(default=None, blank=True, null=True)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    # Les quatre attributs suivant servent uniquement à empêcher les doublons. Mysql n’accepte pas les contraintes Unique sur des champs TextField...
    début = models.CharField(max_length=255)
    fin = models.CharField(max_length=255)
    interdites_début = models.CharField(max_length=255)
    interdites_fin = models.CharField(max_length=255)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ar", "p_détour", "début", "fin", "interdites_début", "interdites_fin"],
                name="Pas de chemins en double.")
        ]
        ordering = ["-dernier_p_modif", "date"]
    
    def __str__(self):
        return f"Étapes : {self.étapes_texte}\n Interdites : {self.interdites_texte}\n p_détour : {self.p_détour}"

    def sauv(self):
        """
        Sauvegarde le chemin si pas déjà présent.
        Si déjà présent, et si un utilisateur est renseigné dans self, met à jour l’utisateur.
        """
        présents = Chemin_d.objects.filter(p_détour=self.p_détour, ar=self.ar, étapes_texte=self.étapes_texte, interdites_texte=self.interdites_texte)
        if présents.exists():
            if self.utilisateur is not None:
                c_d = présents.first()
                c_d.utilisateur=self.utilisateur
                c_d.save()
        else:
            self.save()
            
    def étapes(self):
        return self.étapes_texte.split(";")
    
    def rues_interdites(self):
        return [r for r in self.interdites_texte.split(";") if len(r)>0]
    
    @classmethod
    def of_ligne_csv(cls, ligne, utilisateur=None):
        AR_t, pourcentage_détour_t, étapes_t,rues_interdites_t = ligne.strip().split("|")
        p_détour = int(pourcentage_détour_t)/100.
        AR = bool(AR_t)
        return cls(p_détour=p_détour, ar=AR, étapes_texte=étapes_t, interdites_texte=rues_interdites_t,utilisateur=utilisateur)

    
    @classmethod
    def sauv_csv(cls, chemin=CHEMIN_CHEMINS):
        """
        Enregistre les chemins de la base dans le csv indiqué.
        Attention : pour l’instant cette fonction n’est pas compatible avec of_ligne_csv car elle rajoute les champs utilisateur et zone.
        """
        with open(chemin, "w") as sortie:
            for c in cls.objects.all():
                ligne = "|".join(map(str, (c.ar, c.p_détour, c.étapes_texte, c.interdites_texte, c.utilisateur, c.zone)))
                sortie.write(ligne + "\n")


class Cache_Adresse(models.Model):
    """
    Table d'association ville -> adresse -> chaîne de nœuds
    Note : tout ce qui correspond à des ways dans Nominatim sera enregistré dans la table Rue, via g.nœuds_of_rue.
    Ceci est destiné aux lieux particuliers (bars, bâtiment administratifs, etc. )
    """
    adresse = models.CharField(max_length=200, unique=True)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    nœuds_à_découper = models.TextField()
    def __str__(self):
        return f"{self.adresse}, {self.ville}"
    def nœuds(self):
        return découpe_chaîne_de_nœuds(self.nœuds_à_découper)


class CacheNomRue(models.Model):
    """
    Associe à un nom quelconque de rue son nom osm.
    attribut:
      - nom (str) : nom traité par prétraitement_rue
      - nom_osm (str)
      - ville (Ville)
    Une ligne est ajoutée dans cette table lorsqu’une recherche nominatim sur nom a fourni nom_osm.
    """
    nom = models.CharField(max_length=200)
    nom_osm = models.CharField(max_length=200)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["nom", "ville"], name="Une seule entrée pour chaque (nom, ville).")
        ]

    @classmethod
    def ajoute(cls, nom, nom_osm, ville):
        """
        Effet : Crée si pas déjà présent une entrée du cache. Si une entrée est déjà présente pour (nom, z_d), nom_osm est mis à jour.
        Sortie : l’instance créé ou trouvée.
        """
        essai = cls.objects.filter(nom=nom, ville__nom_complet=ville.nom_complet).first()
        if essai:
            essai.nom=nom_osm
            essai.save()
            return essai
        else:
            res = cls(nom=nom, nom_osm=nom_osm, ville=Ville.objects.get(nom_complet=ville.nom_complet))
            res.save()
            return res


class TypeAmenity(models.Model):
    nom_osm = models.CharField(max_length=200, unique=True)
    nom_français = models.TextField(blank=True, default=None, null=True)

    def __str__(self):
        return self.nom_français


class Amenity(models.Model):
    """
    Pour enregistrer un lieu public, bar, magasin, etc
    texte_tout (str): le dico récupéré d’osm en json
    """
    nom = models.TextField(blank=True, default=None, null=True)
    type_amenity = models.ForeignKey(TypeAmenity, on_delete=models.CASCADE)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    rue = models.ForeignKey(Rue, on_delete=models.CASCADE, blank=True, default=None, null=True)
    lon = models.FloatField()
    lat = models.FloatField()
    horaires = models.TextField(blank=True, default=None, null=True)
    tél = models.TextField(blank=True, default=None, null=True)
    id_osm = models.BigIntegerField(unique=True)
    texte_tout = models.TextField(blank=True, default=None, null=True)

    def coords(self):
        return self.lon, self.lat

    def toutes_les_infos(self):
        """
        Renvoie le dico des données présentes sur osm.
        """
        return json.loads(self.texte_tout)

    def rue_ou_pas(self):
        """
        Renvoie ', nom_de_l_rue' si connue, et '' sinon
        """
        if self.rue:
            return f", {self.rue}"
        else:
            return ""

    def __str__(self):
        return f"{self.nom} ({self.type_amenity}){self.rue_ou_pas()}, {self.ville}"

    @classmethod
    def of_dico(cls, d, v_d):

        champs_obligatoires = ["type", "lon", "lat", "id_osm"]
        if not all(x in d for x in champs_obligatoires):
            raise RuntimeError("Il manquait des champs pour {d} : {(c for c in champs_obligatoires if c not in d)}")
        
        # Champs « normaux »
        champs = {"name":"nom", "lon":"lon", "lat":"lat", "opening_hours":"horaires", "phone":"tél", "id_osm":"id_osm"}
        d_nettoyé = {
            cf: d.get(ce, None)
            for ce, cf in champs.items()
        }
        res = cls(**d_nettoyé)

        # Clefs étrangères
        ta = TypeAmenity.objects.get(nom_osm=d["type"])
        res.type_amenity = ta
        
        res.ville = v_d

        nom_rue = "pas trouvée"
        try:
            nom_rue, _, _ = rue_of_coords((d_nettoyé["lon"], d_nettoyé["lat"]))
            rue = Rue.objects.get(nom_norm=prétraitement_rue(nom_rue), ville=v_d)
            res.rue = rue
        except Exception as e:
            print(f"Problème lors de la récupération de la rue de {d}.\n Ville {v_d}.\n Nom de rue obtenu sur data.gouv.fr : {nom_rue}. Nom normalisé {prétraitement_rue(nom_rue)}\n Erreur : {e}.\n")
        
        # texte_tout
        res.texte_tout = json.dumps(d)
        return res


class Bug(models.Model):
    """
    Pour enregistrer un rapport de bug.
    """
    titre = models.TextField()
    description = models.TextField()
    message_d_erreur = models.TextField(blank=True, default=None, null=True)
    comment_reproduire = models.TextField()
    date = models.DateField(auto_now=True)
    importance = models.SmallIntegerField()

    class meta:
        ordering = ["importance"]
