from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from .forms import MagasinierAuthenticationForm, MagasinierSignupForm, EmployeeSignupForm, DirecteurSignupForm
from django.contrib.auth import login, logout
from .models import  Employee
from produit.models import Produit, Categorie
from transactions.models import Bulletin_de_commande
from django.db.models import Count
# Create your views here.


def magasinier_login(request):
    if request.method == 'POST':

        form = MagasinierAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_magasinier:

                login(request, user)
                return redirect('users:dashboard_magasinier')
            if user.is_employee:

                login(request, user)
                return redirect('users:dashboard_employee')
            if user.is_directeur:

                login(request, user)
                return redirect('users:dashboard_directeur')
        else:
            messages.error(request, 'Invalid login.')
    else:
        form = MagasinierAuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required
@user_passes_test(lambda user: user.is_magasinier)
def dashboard_magasinier(request):
    employee = Employee.objects.get(user=request.user)
    nom = employee.nom
    prenom = employee.prenom
    bulletin_counts = Bulletin_de_commande.objects.values(
        'state').annotate(count=Count('id'))
    bulletins = Bulletin_de_commande.objects.all().order_by('-date')
    produit = Produit.objects.annotate(count=Count('id'))
    categorie = Categorie.objects.annotate(count=Count('id'))
    context = {'bulletin_counts': bulletin_counts, 'bulletins': bulletins,
               'produit': produit, 'categorie': categorie, 'nom': nom, 'prenom': prenom}
    return render(request, 'home.html', context)

@login_required
@user_passes_test(lambda user: user.is_employee)
def dashboard_employee(request):
    employee = Employee.objects.get(user=request.user)
    nom = employee.nom
    prenom = employee.prenom
    bulletin_counts = Bulletin_de_commande.objects.values(
        'state').annotate(count=Count('id')).filter(employe=employee)
    bulletins = Bulletin_de_commande.objects.filter(employe=employee).order_by('-date')
    produit = Produit.objects.annotate(count=Count('id'))
    categorie = Categorie.objects.annotate(count=Count('id'))
    context = {'bulletin_counts': bulletin_counts, 'bulletins': bulletins,
               'produit': produit, 'categorie': categorie, 'nom': nom, 'prenom': prenom}
    return render(request, 'home_employee.html', context)


@login_required
@user_passes_test(lambda user: user.is_directeur)
def dashboard_directeur(request):
    employee = Employee.objects.get(user=request.user)
    nom = employee.nom
    prenom = employee.prenom
    bulletin_counts = Bulletin_de_commande.objects.values(
        'state').annotate(count=Count('id'))
    bulletins = Bulletin_de_commande.objects.all().order_by('-date')
    produit = Produit.objects.annotate(count=Count('id'))
    categorie = Categorie.objects.annotate(count=Count('id'))
    context = {'bulletin_counts': bulletin_counts, 'bulletins': bulletins,
               'produit': produit, 'categorie': categorie, 'nom': nom, 'prenom': prenom}
    return render(request, 'home_directeur.html', context)


@login_required
def logout_user(request):
    logout(request)
    return redirect('users:magasinier_login')

### REGISTRATION USERS ###


def is_superuser(user):
    return user.is_superuser


@login_required
@user_passes_test(is_superuser)
def magasinier_registration(request):
    if request.method == 'POST':
        form = MagasinierSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:magasinier_login')
    else:
        form = MagasinierSignupForm()
    return render(request, 'magasinier_registration.html', {'form': form})


@login_required
@user_passes_test(is_superuser)
def employee_registration(request):
    if request.method == 'POST':
        form = EmployeeSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:magasinier_login')
    else:
        form = EmployeeSignupForm()
    return render(request, 'employee_registration.html', {'form': form})


@login_required
@user_passes_test(is_superuser)
def directeur_registration(request):
    if request.method == 'POST':
        form = DirecteurSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:magasinier_login')
    else:
        form = DirecteurSignupForm()
    return render(request, 'directeur_registration.html', {'form': form})
