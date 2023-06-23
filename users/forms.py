from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Employee, User, Service
from django.db import transaction
from django.contrib.auth.forms import UserCreationForm


class MagasinierAuthenticationForm(AuthenticationForm):
    class Meta:
        model = Employee
        fields = ['username', 'password']


####  Creation des comptes  ####

class MagasinierSignupForm(UserCreationForm):
    nom = forms.CharField(required=True)
    prenom = forms.CharField(required=True)
    matricule = forms.CharField(required=True)
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        widget=forms.Select(attrs={'class': 'w-full'}),
        required=True,  # Make service a required field
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + \
            ('nom', 'prenom', 'matricule',
             'service')  # Include additional fields in form

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_employee = False
        user.is_directeur = False
        user.is_magasinier = True
        if commit:
            user.save()
            magasinier = Employee.objects.create(
                user=user,
                nom=self.cleaned_data.get('nom'),
                prenom=self.cleaned_data.get('prenom'),
                matricule=self.cleaned_data.get('matricule'),
                service=self.cleaned_data.get('service'),
            )
        return user


class EmployeeSignupForm(UserCreationForm):
    nom = forms.CharField(required=True)
    prenom = forms.CharField(required=True)
    matricule = forms.CharField(required=True)
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        widget=forms.Select(attrs={'class': 'w-full'}),
        required=True,  # Make service a required field
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + \
            ('nom', 'prenom', 'matricule',
             'service')  # Include additional fields in form

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_employee = True
        user.is_directeur = False
        user.is_magasinier = False
        if commit:
            user.save()
            magasinier = Employee.objects.create(
                user=user,
                nom=self.cleaned_data.get('nom'),
                prenom=self.cleaned_data.get('prenom'),
                matricule=self.cleaned_data.get('matricule'),
                service=self.cleaned_data.get('service'),
            )
        return user


class DirecteurSignupForm(UserCreationForm):
    nom = forms.CharField(required=True)
    prenom = forms.CharField(required=True)
    matricule = forms.CharField(required=True)
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        widget=forms.Select(attrs={'class': 'w-full'}),
        required=True,  # Make service a required field
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + \
            ('nom', 'prenom', 'matricule',
             'service')  # Include additional fields in form

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_employee = False
        user.is_directeur = True
        user.is_magasinier = False
        if commit:
            user.save()
            magasinier = Employee.objects.create(
                user=user,
                nom=self.cleaned_data.get('nom'),
                prenom=self.cleaned_data.get('prenom'),
                matricule=self.cleaned_data.get('matricule'),
                service=self.cleaned_data.get('service'),
            )
        return user
