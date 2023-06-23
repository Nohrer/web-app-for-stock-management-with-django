from django.db import models
from users.models import Employee
from produit.models import Produit
from django.utils import timezone

# Create your models here.


class Fournisseur(models.Model):
    nom = models.CharField(max_length=200)
    adresse = models.CharField(max_length=200)
    telephone = models.CharField(max_length=10)

    def __str__(self):
        return self.nom


class Bulletin_de_commande(models.Model):
    DEMANDER = 'demander'
    APPROVER = 'approver'
    TRAITER = 'traiter'
    SUPPRIMER = 'supprimer'
    STATE_CHOICES = [
        (DEMANDER, 'Demander'),
        (APPROVER, 'Approver'),
        (SUPPRIMER, 'Supprimer'),
        (TRAITER, 'Traiter'),
    ]

    date = models.DateField(default=timezone.now)
    state = models.CharField(
        max_length=20, choices=STATE_CHOICES, default=DEMANDER)
    produits_demandes = models.ManyToManyField(
        Produit, through='DemandeDeProduit')
    employe = models.ForeignKey(
        Employee, on_delete=models.PROTECT, default=0)

    def quantite_demande(self):
        demande_total = 0
        for demande in self.demandedeproduit_set.all():
            demande_total += demande.quantite_demande
        return demande_total


class DemandeDeProduit(models.Model):
    bulletin = models.ForeignKey(
        Bulletin_de_commande, on_delete=models.CASCADE)
    produit_demande = models.ForeignKey(Produit, on_delete=models.CASCADE,null=False)
    quantite_demande = models.IntegerField(null=False)
    quantite_fournie = models.IntegerField(null=True, blank=True)
    date_sortie = models.DateField(default=timezone.now)


class type_bl(models.Model):
    typpe = models.CharField(max_length=200)

    def __str__(self) -> str:
        return str(self.typpe)


class Bonne_livraison(models.Model):
    date = models.DateField()
    produit = models.ManyToManyField(
        Produit, through='EntreeDeProduit')
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.CASCADE)
    type_bl = models.ForeignKey(type_bl, on_delete=models.CASCADE)


class EntreeDeProduit(models.Model):
    bl = models.ForeignKey(
        Bonne_livraison, on_delete=models.CASCADE)
    produit_entree = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite_entree = models.IntegerField()
