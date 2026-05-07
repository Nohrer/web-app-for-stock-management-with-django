from django.forms import ModelForm, inlineformset_factory

from .models import (
    Bulletin_de_commande,
    DemandeDeProduit,
    Bonne_livraison,
    EntreeDeProduit,
    type_bl,
    Fournisseur,
    DemandeApprovisionnement,
    DemandeApprovisionnementLigne,
)
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
        fields = (
            'nom',
            'adresse',
            'telephone',
            'email',
            'categories',
            'delai_livraison_jours',
            'prix_reference',
            'note',
        )
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'}),
            'adresse': forms.TextInput(attrs={'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'}),
            'telephone': forms.TextInput(attrs={'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'}),
            'email': forms.EmailInput(attrs={'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'}),
            'delai_livraison_jours': forms.NumberInput(attrs={'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'}),
            'prix_reference': forms.NumberInput(attrs={'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500', 'step': '0.01'}),
            'note': forms.Textarea(attrs={'rows': 4, 'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'}),
            'categories': forms.CheckboxSelectMultiple(),
        }


class DemandeApprovisionnementForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Categorie.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'w-full rounded-xl border-slate-300 shadow-sm', 'id': 'id_categories'}),
    )
    fournisseurs = forms.ModelMultipleChoiceField(
        queryset=Fournisseur.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = DemandeApprovisionnement
        fields = (
            'date',
            'categorie',
            'delai_max_jours',
            'objet',
            'message',
            'fournisseurs',
        )
        widgets = {
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'}),
            'categorie': forms.HiddenInput(),
            'delai_max_jours': forms.NumberInput(attrs={'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'}),
            'objet': forms.TextInput(attrs={'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'}),
            'message': forms.Textarea(attrs={'rows': 4, 'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'}),
            'fournisseurs': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, fournisseurs_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fournisseurs'].queryset = fournisseurs_queryset or Fournisseur.objects.none()
        # Make categorie optional in the form so it doesn't block validation if empty
        self.fields['categorie'].required = False
        # if the form was initialized with an instance, populate categories initial
        if self.instance and self.instance.pk:
            try:
                self.fields['categories'].initial = [self.instance.categorie.pk]
            except Exception:
                self.fields['categories'].initial = []

    def clean(self):
        cleaned = super().clean()
        # The model requires `categorie` (single FK), but the form exposes `categories`
        # (multi-select). If no `categorie` was provided directly, derive it from
        # the first selected category so the model validation passes.
        if not cleaned.get('categorie'):
            cats = cleaned.get('categories')
            if cats:
                # Set categorie from the first selected category
                self.cleaned_data['categorie'] = cats[0]
            else:
                # both empty — surface a clear error on categories
                self.add_error('categories', 'Veuillez sélectionner au moins une catégorie.')
        return self.cleaned_data


class DemandeApprovisionnementLigneForm(forms.ModelForm):
    class Meta:
        model = DemandeApprovisionnementLigne
        fields = ('produit', 'quantite')
        widgets = {
            'produit': forms.Select(attrs={'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'}),
            'quantite': forms.NumberInput(attrs={'class': 'w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'}),
        }


DemandeApprovisionnementLigneFormSet = inlineformset_factory(
    DemandeApprovisionnement,
    DemandeApprovisionnementLigne,
    form=DemandeApprovisionnementLigneForm,
    fields=('produit', 'quantite'),
    extra=1,
    can_delete=False,
)