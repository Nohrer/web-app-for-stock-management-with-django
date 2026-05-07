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


def _build_category_filter_options(categories_qs):
    """Build one select options list with disabled main-category headers and selectable sub-categories."""
    category_hierarchy = {
        'X.All commodities': [
            'EQUIPEMENT (EQUIPMENT, SERVICE & SPARES)',
            'ELECTRICITE & INSTRUMENTATION (EQUIPMENT, SERVICE/INSTALLATION & SPARES)',
            'INDUSTRIAL MAINTENANCE, EXTERNALISATION AND LOGICTICS',
            'ARCHITECTURAL SERVICES',
            'LANDSCAPING AND GARDENING',
            'AUXILIARY MATERIAL AND UTILITIES',
            'BULK SUPPLY',
            'IT & TELECOM',
            'Construction & Buildings',
            'Equipements (Equipement, Service and Spares)',
            'Electricity & Instrumentation (Equipement, Service/installation and Spares)',
            'Industrial Maintenance, Externalisation and Logistics',
            'Intelectual Services',
            'Facility Management',
            'Additives/Auxiliary Material and Utilities',
            'Bulk supply',
            'IT & Telecom',
            'Duplicate Commodities',
            'SAP Commodities',
        ],
        'A.Structural Mechanical Piping': [
            'SMP General Contracting',
            'Piping works',
            'Structural works',
            'Mechanical works',
            'Industrial specialities',
        ],
        'B.Electrical & Instrumentation': [
            'Electrical works',
            'E&I General Contracting',
        ],
        'C.Civil Works': [
            'Earthworks',
            'Concrete Works',
            'Building & Structures',
            'Roads & Infrastructure',
            'Temporary & Anxillary Works',
            'Civil General Contracting',
        ],
        'D.Equipment': [
            'Static Equipment',
            'Rotating Equipment',
            'Process Equipment',
            'Air & Gas Systems',
            'Utilities Equipment',
            'Lifting Equipment',
            'Handling Equipment',
            'Separation Equipment',
            'Packaged Units & Skids',
            'Electrical & Power Systems',
            'Instrumentation & Control Systems',
            'Piping Materials',
            'Inspection & Testing Services',
            'Piping Supervision Services',
            'Fabrication & Manufacturing Services',
        ],
    }

    categories_by_name = {c.nom: c for c in categories_qs}
    options = []
    used_ids = set()

    def add_group(header_name, fallback_sub_names):
        header_category = categories_by_name.get(header_name)
        if header_category is None:
            return

        options.append({'value': '', 'label': header_name, 'disabled': True})

        child_categories = list(header_category.subcategories.all().order_by('nom'))
        for sub_name in fallback_sub_names:
            fallback_category = categories_by_name.get(sub_name)
            if fallback_category is not None and fallback_category.parent_id is None:
                child_categories.append(fallback_category)

        seen_child_ids = set()
        for category_obj in sorted(child_categories, key=lambda item: item.nom):
            if category_obj.id in used_ids or category_obj.id in seen_child_ids:
                continue
            options.append({'value': str(category_obj.id), 'label': f'  - {category_obj.nom}', 'disabled': False})
            used_ids.add(category_obj.id)
            seen_child_ids.add(category_obj.id)

    for head, sub_categories in category_hierarchy.items():
        add_group(head, sub_categories)

    # Keep any other categories reachable in the filter.
    remaining = [c for c in categories_qs if c.id not in used_ids and c.nom not in category_hierarchy]
    if remaining:
        options.append({'value': '', 'label': 'Autres catégories', 'disabled': True})
        for category_obj in remaining:
            options.append({'value': str(category_obj.id), 'label': f'  - {category_obj.nom}', 'disabled': False})

    return options


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
    categories = Categorie.objects.all().order_by('nom')
    category_filter_options = _build_category_filter_options(categories)
    products = Produit.objects.all()
    selected_category_id = request.GET.get('categorie_id', '')
    page_number = request.GET.get('page', 1)

    if selected_category_id:
        products = products.filter(categorie_id=selected_category_id)

    paginator = Paginator(products, 8)
    page_obj = paginator.get_page(page_number)

    return render(request, 'produit_list.html', {
        'products': page_obj,
        'categories': categories,
        'category_filter_options': category_filter_options,
        'nom': nom,
        'prenom': prenom,
        'employee': employee,
        'page_temp': page_temp,
        'selected_category_id': str(selected_category_id),
    })


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

    categories = Categorie.objects.all().order_by('nom')
    category_filter_options = _build_category_filter_options(categories)

    # Get the selected category and user input query
    selected_category_id = request.GET.get('categorie_id', '')
    query = request.GET.get('q', '')

    if selected_category_id:
        # If a category is selected, filter the products by that category
        products = Produit.objects.filter(categorie_id=selected_category_id)

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
    return render(request, 'search_product.html', {
        'products': products,
        'categories': categories,
        'category_filter_options': category_filter_options,
        'nom': nom,
        'prenom': prenom,
        'page_temp': page_temp,
        'selected_category_id': str(selected_category_id),
    })


@login_required
@user_passes_test(lambda user: user.is_magasinier or user.is_directeur)
def ajouter(request):
    employee = Employee.objects.get(user=request.user)
    if employee.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
    else:
        page_temp = 'dashboard.html'

    categories = Categorie.objects.all()
    category_filter_options = _build_category_filter_options(categories.order_by('nom'))
    main_category_names = [
        'X.All commodities',
        'A.Structural Mechanical Piping',
        'B.Electrical & Instrumentation',
        'C.Civil Works',
        'D.Equipment',
    ]
    main_categories = Categorie.objects.filter(nom__in=main_category_names).order_by('nom')
    form = ProduitForm()  # Initialize with an empty form
    selected_category_id = request.POST.get('categorie', '')

    if request.method == 'POST':
        if 'ajouter_categorie' in request.POST:
            # Code for adding a category or sub-category
            nom = request.POST.get('nom')
            description = request.POST.get('description')
            parent_id = request.POST.get('parent_category') or None
            magasin = Magasin.objects.get(id=1)
            parent = Categorie.objects.filter(pk=parent_id).first() if parent_id else None
            category = Categorie(
                nom=nom,
                description=description,
                magasin=magasin,
                parent=parent,
            )
            category.save()
            if parent:
                messages.success(request, 'Sous-catégorie ajoutée avec succès!')
            else:
                messages.success(request, 'Catégorie principale a été ajoutée!')
            return redirect('produit:product_list')
        elif 'ajouter_produit' in request.POST:
            # Code for adding a product
            form = ProduitForm(request.POST)
            if form.is_valid():
                produit = form.save()
                messages.success(request, 'Produit a été ajouté!')
                return redirect('produit:product_list')
    nom = employee.nom
    prenom = employee.prenom
    return render(request, 'ajouter_produit.html', {
        'form': form,
        'categories': categories,
        'category_filter_options': category_filter_options,
        'main_categories': main_categories,
        'selected_category_id': str(selected_category_id),
        'nom': nom,
        'prenom': prenom,
        'page_temp': page_temp,
    })


@login_required
@user_passes_test(lambda user: user.is_magasinier or user.is_directeur)
def product_state(request):
    employee = Employee.objects.get(user=request.user)
    if employee.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
    else:
        page_temp='dashboard.html'
    categories = Categorie.objects.all()
    category_filter_options = _build_category_filter_options(categories)

    nom = employee.nom
    prenom = employee.prenom
    selected_category_id = request.POST.get('categorie_id', '')
    selected_date = request.POST.get('date', '')
    if request.method == 'POST':
        date = request.POST.get('date')
        if date:
            date_str = datetime.strptime(date, '%Y-%m-%d')
            produits = Produit.history.as_of(
                datetime.strptime(date, '%Y-%m-%d'))
            if selected_category_id:
                produits = produits.filter(categorie_id=selected_category_id)
            context = {'date': date_str, 'produits': produits,
                       'nom': nom, 'prenom': prenom,'page_temp':page_temp,'categories':categories,'category_filter_options': category_filter_options,'selected_category_id': str(selected_category_id),'selected_date': selected_date}
            return render(request, 'produit_state.html', context)
        else:
            return render(request, 'produit_state.html', {'nom': nom, 'prenom': prenom,'page_temp':page_temp ,'categories':categories,'category_filter_options': category_filter_options,'selected_category_id': str(selected_category_id),'selected_date': selected_date})
    else:
        return render(request, 'produit_state.html', {'nom': nom, 'prenom': prenom,'page_temp':page_temp ,'categories':categories,'category_filter_options': category_filter_options,'selected_category_id': str(selected_category_id),'selected_date': selected_date})
