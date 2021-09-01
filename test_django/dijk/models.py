from django.db import models

# Create your models here.


class Ville(models.Model):
    nom_complet = models.CharField(max_length=100)
    nom_norm = models.CharField(max_length=100)
    code = models.IntegerField()
    def __str__(self):
        return self.nom_complet


class Rue(models.Model):
    nom_complet = models.CharField(max_length=200)
    nom_norm = models.CharField(max_length=200)
    def __str__(self):
        return self.nom_complet
    

class Sommet(models.Model):
    
    id_osm = models.IntegerField()
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.id_osm)

    def voisins(self):
        arêtes = Arête.objects.get(départ=self.id)
        return [(a.arrivée.id_osm, a.longueur) for a in arêtes]

    
class Arête(models.Model):
    départ = models.ForeignKey(Sommet, related_name="sommet_départ", on_delete=models.CASCADE)
    arrivée = models.ForeignKey(Sommet, related_name="sommet_arrivée", on_delete=models.CASCADE)
    longueur = models.FloatField()
    cycla = models.FloatField(default=1.0)
    rue = models.ForeignKey(Rue, on_delete=models.CASCADE) # Si plusieurs rues : séparées par un point-virgule.
    def __str__(self):
        return f"({self.départ}, {self.arrivée})"

    
class Nœud_of_Rue(models.Model):
    """ table d'association ville -> rue -> nœud """
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    rue = models.ForeignKey(Rue, on_delete=models.CASCADE)
    nœud = models.ForeignKey(Sommet, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.ville}, {self.rue}, {self.nœud}"

    
class Cache_Adresse(models.Model):
    """ Table d'association ville -> adresse -> sommet
    Un seul sommet par ligne"""
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    adresse = models.CharField(max_length=200)
    nœud = models.ForeignKey(Sommet, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.ville}, {self.adresse}, {self.nœud}"
