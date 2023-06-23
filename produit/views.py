from django.shortcuts import render
from django.views.generic import View
from django.db.models import Q
from .models import Produit, Categorie, Magasin
from transactions.models import DemandeDeProduit, EntreeDeProduit, Bulletin_de_commande, Bonne_livraison
from users.models import  Employee
from django.contrib.auth.decorators import user_passes_test, login_required
from .forms import ProduitForm, CategorieForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, OuterRef, Subquery
from django.db import models
from datetime import datetime
from django.utils import timezone

# Create your views here.


@login_required
@user_passes_test(lambda user: user.is_magasinier or user.is_directeur)
def product_list(request):
    employee = Employee.objects.get(user=request.user)
    if employee.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
    else:
        page_temp='dashboard.html'
        
    nom = employee.nom
    prenom = employee.prenom
    categories = Categorie.objects.all()
    products = Produit.objects.all()
    selected_category = request.GET.get('categorie')
    page_number = request.GET.get('page', 1)
    paginator = Paginator(products, 8)

    if selected_category:
        products = products.filter(categorie__nom=selected_category)

    paginator = Paginator(products, 8)
    page_obj = paginator.get_page(page_number)

    return render(request, 'produit_list.html', {'products': page_obj, 'categories': categories, 'nom': nom, 'prenom': prenom ,'employee':employee ,'page_temp':page_temp,'selected_category':selected_category})


@login_required
@user_passes_test(lambda user: user.is_magasinier or user.is_directeur)
def search_product(request):
    
    employee = Employee.objects.get(user=request.user)
    if employee.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
    else:
        page_temp='dashboard.html'
     
    nom = employee.nom
    prenom = employee.prenom

    categories = Categorie.objects.all()

    # Get the selected category and user input query
    selected_category = request.GET.get('categorie')
    query = request.GET.get('q', '')

    if selected_category:
        # If a category is selected, filter the products by that category
        products = Produit.objects.filter(categorie__nom=selected_category)

        if query:
            # If there is a user input query, further filter the products by the query
            products = products.filter(
                Q(libelle__icontains=query)
                | Q(reference__icontains=query)
                | Q(detaille__icontains=query)
            )
    else:
        # If no category is selected, filter the products by the user input query only
        products = Produit.objects.filter(
            Q(libelle__icontains=query)
            | Q(reference__icontains=query)
            | Q(detaille__icontains=query)
        )
    return render(request, 'search_product.html', {'products': products, 'categories': categories, 'nom': nom, 'prenom': prenom,'page_temp':page_temp,'selected_category':selected_category})


@login_required
@user_passes_test(lambda user: user.is_magasinier)
def ajouter(request):
    categories = Categorie.objects.all()
    form = ProduitForm()  # Initialize with an empty form

    if request.method == 'POST':
        if 'ajouter_categorie' in request.POST:
            # Code for adding a category
            nom = request.POST.get('nom')
            description = request.POST.get('description')
            magasin = Magasin.objects.get(id=1)
            category = Categorie(
                nom=nom, description=description, magasin=magasin)
            category.save()
            messages.success(request, 'Catégorie a été ajoutée!')
            return redirect('produit:product_list')
        elif 'ajouter_produit' in request.POST:
            # Code for adding a product
            form = ProduitForm(request.POST)
            if form.is_valid():
                produit = form.save()
                messages.success(request, 'Produit a été ajouté!')
                return redirect('produit:product_list')
    employe = Employee.objects.get(user=request.user)
    nom = employe.nom
    prenom = employe.prenom
    return render(request, 'ajouter_produit.html', {'form': form, 'categories': categories, 'nom': nom, 'prenom': prenom})


@login_required
@user_passes_test(lambda user: user.is_magasinier or user.is_directeur)
def product_state(request):
    employee = Employee.objects.get(user=request.user)
    if employee.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
    else:
        page_temp='dashboard.html'
    categories = Categorie.objects.all()

    nom = employee.nom
    prenom = employee.prenom
    if request.method == 'POST':
        date = request.POST.get('date')
        date_str = datetime.strptime(date, '%Y-%m-%d')
        categories_selected = request.POST.getlist('categories')
        if date:
            produits = Produit.history.as_of(
                datetime.strptime(date, '%Y-%m-%d'))
            if categories_selected:
                produits = produits.filter(categorie__in=categories_selected)
            context = {'date': date_str, 'produits': produits,
                       'nom': nom, 'prenom': prenom,'page_temp':page_temp,'categories':categories}
            return render(request, 'produit_state.html', context)
        else:
            return render(request, 'produit_state.html', {'nom': nom, 'prenom': prenom,'page_temp':page_temp ,'categories':categories})
    else:
        return render(request, 'produit_state.html', {'nom': nom, 'prenom': prenom,'page_temp':page_temp ,'categories':categories})
