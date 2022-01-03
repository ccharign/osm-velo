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
    nom_complet = models.CharField(max_length=200)
    nom_norm = models.CharField(max_length=200)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE )
    nœuds_à_découper = models.CharField(max_length=2000) #chaîne de caractères contenant les nœuds à splitter
    def __str__(self):
        return f"{self.nom_complet} ({self.ville})"
    def nœuds(self):
        return tuple(map(int, self.nœuds_à_découper.split(",")))
    

class Sommet(models.Model):
    
    id_osm = models.IntegerField()
    lon = models.FloatField()
    lat = models.FloatField()
    
    def __str__(self):
        return str(self.id_osm)

    def voisins(self):
        arêtes = Arête.objects.get(départ=self.id)
        return [(a.arrivée.id_osm, a.longueur) for a in arêtes]

    
class Ville_of_Sommet(models.Model):
    """ Table d’association sommet -> ville (il peut y avoir plusieurs villes par sommet)"""
    sommet = models.ForeignKey(Sommet, on_delete=models.CASCADE )
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE )
    

# class Nœud_of_Rue(models.Model):
#     """ table d'association ville -> rue -> nœud """
#     ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
#     rue = models.ForeignKey(Rue, on_delete=models.CASCADE)
#     nœud = models.ForeignKey(Sommet, on_delete=models.CASCADE)
#     def __str__(self):
#         return f"{self.ville}, {self.rue}, {self.nœud}"

    
class Arête(models.Model):
    départ = models.ForeignKey(Sommet, related_name="sommet_départ", on_delete=models.CASCADE)
    arrivée = models.ForeignKey(Sommet, related_name="sommet_arrivée", on_delete=models.CASCADE)
    longueur = models.FloatField()
    cycla = models.FloatField(default=1.0)
    rue = models.ManyToManyField(Rue)
    def __str__(self):
        return f"({self.départ}, {self.arrivée})"

    
class Chemin_d(models.Model):
    ar = models.BooleanField(default=False)
    étapes = models.TextField(null=False)
    p_détour = models.FloatField()
    p_modif = models.FloatField()
    interdites = models.TextField()

    
class Cache_Adresse(models.Model):
    """ Table d'association ville -> adresse -> sommet
    Un seul sommet par ligne"""
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    adresse = models.CharField(max_length=200)
    nœud = models.ForeignKey(Sommet, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.ville}, {self.adresse}, {self.nœud}"
