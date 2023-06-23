
from django import forms
from .models import Categorie, Produit


class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom', 'description']


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['libelle', 'reference',
                  'categorie', 'detaille']
