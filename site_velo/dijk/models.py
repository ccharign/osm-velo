from django.db import models

# Create your models here.


def découpe_chaîne_de_nœuds(c):
    return tuple(map(int, c.split(",")))



    
class Ville(models.Model):
    nom_complet = models.CharField(max_length=100)
    nom_norm = models.CharField(max_length=100)
    code = models.IntegerField()
    def __str__(self):
        return self.nom_complet

class Zone(models.Model):
    """
    Une zone délimite une zone dont le graphe sera mis en mémoire au chargement.
    """
    nom = models.CharField(max_length=100, unique=True)
    ville_défaut = models.ForeignKey(Ville, on_delete=models.CASCADE)

class Sommet(models.Model):
    
    id_osm = models.IntegerField(unique=True)
    lon = models.FloatField()
    lat = models.FloatField()
    zone = models.ManyToManyField(Zone)
    
    def __str__(self):
        return str(self.id_osm)

    # Sert dans les tas de Dijkstra au cas où deux sommets aient exactement la même distance au départ
    def __lt__(self, autre):
        return self.id_osm < autre
    # def __gt__(self, autre):
    #     return False

    def __hash__(self):
        return self.id_osm

    def voisins(self, p_détour):
        arêtes = Arête.objects.filter(départ=self).select_related("arrivée")
        return [(a.arrivée, a.longueur_corrigée(p_détour)) for a in arêtes]

    def voisins_nus(self):
        arêtes = Arête.objects.filter(départ=self)
        return [a.arrivée for a in arêtes]

    def coords(self):
        return self.lon, self.lat
    
#https://docs.djangoproject.com/en/3.2/topics/db/examples/many_to_many/
class Rue(models.Model):
    """
    Une entrée pour chaque couple (rue, ville) : certaines rues peuvent apparaître en double.
    """
    nom_complet = models.CharField(max_length=200)
    nom_norm = models.CharField(max_length=200)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE )
    nœuds_à_découper = models.TextField() #chaîne de caractères contenant les nœuds à splitter

    class Meta:
        constraints=[
            models.UniqueConstraint(fields=["nom_norm", "ville"], name = "une seule rue pour chaque nom_norm pour chaque ville.")
        ]
    
    def __str__(self):
        return f"{self.nom_complet} ({self.ville})"
    def nœuds(self):
        return découpe_chaîne_de_nœuds(self.nœuds_à_découper)

    
class Arête(models.Model):
    """
    Attributs:
        départ (Sommet)
        arrivée (Sommet)
        longueur (float)
        cycla (float) : cyclabilité calculée par l'IA. None par défaut.
        cycla_défaut (float) : cyclabilité obtenue par les données présentes dans osm. À terme dépendra de zone 30, piste cyclable, etc. Pour l'instant c'est 1.
        rue (Rue). Ce champ est-il utile ?
        geom (string). Couples lon,lat séparés par des ;
        nom (str)
        zone (Zone)
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
        assert cy>0, f"cyclabilité ⩽ pour l’arête {self}"
        return self.longueur / cy**( p_détour*1.5)

    # def inverse(self):
    #     """
    #     Renvoie l’arête inverse. Elle a une cyclabilité_défaut de .8 * self.cycla_défaut
    #     """
    #     return Arête(
    #         départ=self.arrivée,
    #         arrivée=self.départ,
    #         nom=self.nom,
    #         longueur=self.longueur,
    #         #zone=self.zone, # À faire après coup, en cas de bulk_create
    #         cycla_défaut=.8*self.cycla_défaut,
    #         #rue=self.rue,
    #         geom=self.geom,
    #         sensInterdit=True
    #     )
    
    

    
class Cache_Adresse(models.Model):
    """ 
    Table d'association ville -> adresse -> chaîne de nœuds
    Note : tout ce qui correspond à des ways dans Nominatim sera enregistré dans la table Rue, via g.nœuds_of_rue.
    """
    adresse = models.CharField(max_length=200, unique=True)
    nœuds_à_découper = models.TextField()
    def __str__(self):
        return f"{self.ville}, {self.adresse}, {self.nœud}"
    def nœuds(self):
        return découpe_chaîne_de_nœuds(self.nœuds_à_découper)


class Chemin_d(models.Model):
    """
    Attributs:
        - ar (bool)
        - p_détour (float) proportion détour
        - étapes_texte (str)
        - interdites (str)
        - utilisateur (str)
        - dernier_p_modif (float) : nb d’arêtes modifiées / distance entre départ et arrivée lors du dernier apprentissage.
    """
    ar=models.BooleanField(default=False)
    p_détour=models.FloatField()
    étapes_texte=models.TextField()
    interdites_texte=models.TextField(default=None, blank=True, null=True)
    utilisateur = models.CharField(max_length=100, default=None, blank=True, null=True)
    dernier_p_modif = models.FloatField(default=None, blank=True, null=True)
    # def étapes(self):
    #     return map(Étape, self.étapes_texte.split(";"))
    # def interdites(self):
    #     return map(Étape, self.interdites_texte.split(";"))
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=["ar", "p_détour", "étapes_texte", "interdites_texte"], name = "Pas de chemins en double.")
        ]
    
    def __str__(self):
        é = self.étapes
        return é[0] + "-->" + é[-1]

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
            
    
    @classmethod
    def of_ligne_csv(cls, ligne, utilisateur=None):
        AR_t, pourcentage_détour_t, étapes_t,rues_interdites_t = ligne.strip().split("|")
        p_détour = int(pourcentage_détour_t)/100.
        AR = bool(AR_t)
        return cls(p_détour=p_détour, ar=AR, étapes_texte=étapes_t, interdites_texte=rues_interdites_t,utilisateur=utilisateur)
