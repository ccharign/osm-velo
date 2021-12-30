from django.db import models

# Create your models here.


class Ville(models.Model):
    nom_complet = models.CharField(max_length=100)
    nom_norm = models.CharField(max_length=100)
    code = models.IntegerField()
    def __str__(self):
        return self.nom_complet

#https://docs.djangoproject.com/en/3.2/topics/db/examples/many_to_many/
class Rue(models.Model):
    """
    Une entrée pour chaque couple (rue, ville) : certaines rues peuvent apparaître en double.
    """
    nom_complet = models.CharField(max_length=200)
    nom_norm = models.CharField(max_length=200)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE )
    nœuds_à_découper = models.TextField() #chaîne de caractères contenant les nœuds à splitter
    def __str__(self):
        return f"{self.nom_complet} ({self.ville})"
    def nœuds(self):
        return tuple(map(int, self.nœuds_à_découper.split(",")))


class Sommet(models.Model):
    
    id_osm = models.IntegerField(unique=True)
    lon = models.FloatField()
    lat = models.FloatField()
    
    def __str__(self):
        return str(self.id_osm)

    # Sert dans les tas de Dijkstra au cas où deux sommets aient exactement la même distance au départ
    def __lt__(self, autre):
        return True
    def __gt__(self, autre):
        return False

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
    

# Passage à un many_to_many de Django

# class Ville_of_Sommet(models.Model):
#     """ Table d’association sommet -> ville (il peut y avoir plusieurs villes par sommet)"""
#     sommet = models.ForeignKey(Sommet, on_delete=models.CASCADE )
#     ville = models.ForeignKey(Ville, on_delete=models.CASCADE )
    
# class Nœud_of_Rue(models.Model):
#     """ table d'association ville -> rue -> nœud """
#     ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
#     rue = models.ForeignKey(Rue, on_delete=models.CASCADE)
#     nœud = models.ForeignKey(Sommet, on_delete=models.CASCADE)
#     def __str__(self):
#         return f"{self.ville}, {self.rue}, {self.nœud}"

    
class Arête(models.Model):
    """
    Attributs:
        départ (Sommet)
        arrivée (Sommet)
        cycla (float) : cyclabilité calculée par l'IA. None par défaut.
        cycla_défaut (float) : cyclabilité obtenue par les données présentes dans osm. À terme dépendra de zone 30, piste cyclable, etc. Pour l'instant c'est 1.
        longueur (float)
        rue (Rue)
        geom (string). Couples lon,lat séparés par des ;
    """
    départ = models.ForeignKey(Sommet, related_name="sommet_départ", on_delete=models.CASCADE, db_index=True)
    arrivée = models.ForeignKey(Sommet, related_name="sommet_arrivée", on_delete=models.CASCADE)
    longueur = models.FloatField()
    cycla = models.FloatField(blank=True, null=True, default=None)
    cycla_défaut = models.FloatField(default=1.0)
    rue = models.ManyToManyField(Rue)
    geom = models.TextField()
    nom = models.CharField(max_length=200, blank=True, null=True, default=None)

    def __str__(self):
        return f"({self.départ}, {self.arrivée})"

    def géométrie(self):
        """
        Renvoie une liste de (lon,lat) qui décrit la géométrie de l'arête.
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
    
    # def longueur_corrigée(self, p_détour):
    #     """
    #     Entrée : p_détour (float), proportion de détour.
    #     Sortie : Longueur corrigée par la cyclabilité.
    #     """
    #     cy = self.cyclabilité()
    #     return self.longueur / cy**( p_détour*1.5)
    
    


    
class Cache_Adresse(models.Model):
    """ Table d'association ville -> adresse -> sommet
    Un seul sommet par ligne"""
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    adresse = models.CharField(max_length=200)
    nœud = models.ForeignKey(Sommet, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.ville}, {self.adresse}, {self.nœud}"
