from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):
    is_magasinier = models.BooleanField(default=False)
    is_employee = models.BooleanField(default=True)
    is_directeur = models.BooleanField(default=False)


class Service(models.Model):
    nom = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.nom


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    matricule = models.CharField(max_length=100)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.nom + " " + self.prenom

    def full_name(self):
        return self.nom + " " + self.prenom


