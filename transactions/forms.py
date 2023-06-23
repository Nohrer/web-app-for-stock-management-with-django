from django.forms import ModelForm, inlineformset_factory

from .models import Bulletin_de_commande, DemandeDeProduit, Bonne_livraison, EntreeDeProduit, type_bl, Fournisseur
from produit.models import Categorie
from users.models import Employee
from django import forms
from django.utils import timezone


class BulletinForm(ModelForm):
    date = forms.DateField(initial=timezone.now().date())
    input_attrs = {
        'class': 'w-1/3 h-10  border-amber-400 rounded-md shadow-sm text-slate-800 focus:text-slate-950 pl-2 pr-16'
    }
    employe = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.Select(attrs={
            **input_attrs,
            'size': 1,
        }),
    )

    class Meta:
        model = Bulletin_de_commande
        fields = ['date', 'state', 'employe']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}

DemandeFormSet = inlineformset_factory(Bulletin_de_commande, DemandeDeProduit, fields=(
    'produit_demande', 'quantite_demande'), extra=1, can_delete=False)


class DemandeDeProduitForm(forms.ModelForm):
    class Meta:
        model = DemandeDeProduit
        fields = ['quantite_demande']
        widgets = {
            'quantite_demande': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class BonForm(ModelForm):
    input_attrs = {
        'class': 'w-full border-slate-300 rounded-md shadow-sm text-slate-400 focus:text-slate-950 py-2'}

    date = forms.DateField(
        widget=forms.DateInput(attrs={
            **input_attrs,
            'type': 'date',
        }),
        initial=timezone.now().date(),
    )
    fournisseur = forms.ModelChoiceField(
        queryset=Fournisseur.objects.all(),
        widget=forms.Select(attrs=input_attrs),
    )
    type_bl = forms.ModelChoiceField(
        queryset=type_bl.objects.all(),
        widget=forms.Select(attrs=input_attrs),
    )

    class Meta:
        model = Bonne_livraison
        fields = ['date', 'fournisseur', 'type_bl']

    class Meta:
        model = Bonne_livraison
        fields = ['date', 'fournisseur', 'type_bl']


EntreeDeProduitFormSet = inlineformset_factory(
    Bonne_livraison, EntreeDeProduit,  fields=(
        'produit_entree', 'quantite_entree'), extra=1, can_delete=False
)


class EntreeDeProduitForm(forms.ModelForm):
    produit_entree=forms.CharField(required=True)
    quantite_entree=forms.IntegerField(required=True)
    class Meta:
        model = EntreeDeProduit
        fields = (
            'produit_entree',
            'quantite_entree'
        )
        widgets = {
            'produit_entree': forms.TextInput(attrs={'class': 'form-control,'}),
            'quantite_entree': forms.NumberInput(attrs={'class': 'form-control'}),

        }
        error_messages = {
            'quantite_entree': {'required': "La quantité d'entrée est requise."},
            'produit_entree': {'required': "Le produit d'entrée est requise."},
        }
        empty_value=None


class DateRangeForm(forms.Form):
    input_attrs = {
        'class': 'w-full border-slate-300 rounded-md shadow-sm text-slate-400 focus:text-slate-950'}
    input_attrs2={
        'class': 'border-amber-400 rounded-md shadow-sm text-slate-800 focus:text-slate-950'}
    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={
            **input_attrs,
            'type': 'date',
        }),
    )

    date_fin = forms.DateField(
        widget=forms.DateInput(attrs={
            **input_attrs,
            'type': 'date',
        }),
        initial=timezone.now().date(),
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=Categorie.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            **input_attrs2,
         'size':1,
            
        }),
        required=False,
    )


class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ('nom', 'adresse', 'telephone')