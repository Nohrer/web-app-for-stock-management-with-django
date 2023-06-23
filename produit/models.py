from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

# Create your models here.


class Magasin(models.Model):

    def __str__(self):
        return str(self.id)


class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    magasin = models.ForeignKey(Magasin, on_delete=models.CASCADE)

    def __str__(self):
        return self.nom


class Produit(models.Model):
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE)
    libelle = models.CharField(max_length=200)
    reference = models.CharField(max_length=200)
    quantite = models.IntegerField(default=0)
    detaille = models.TextField(blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.libelle

    def acronym(self):
        if self.detaille != "":
            return self.detaille[:6]+".."
        else:
            return '/'
