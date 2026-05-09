from django.urls import reverse
from django.template.loader import get_template
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.db import models
import json
from .models import (
    Bulletin_de_commande,
    DemandeDeProduit,
    Bonne_livraison,
    EntreeDeProduit,
    DemandeApprovisionnement,
    DemandeApprovisionnementLigne,
)
from django.forms import inlineformset_factory
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from produit.models import Produit, Categorie
from users.models import Employee
from django.db.models import Q, Count
from django.utils import timezone
from urllib.parse import quote, urlencode
from .forms import (
    BulletinForm,
    EntreeDeProduitFormSet,
    BonForm,
    DateRangeForm,
    FournisseurForm,
    DemandeApprovisionnementForm,
    DemandeApprovisionnementLigneFormSet,
)
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required,user_passes_test
from django.core.paginator import Paginator
from django.db.models import Sum
from .models import Fournisseur


def _build_category_filter_options(categories_qs):
    """Build a single hierarchical category select matching the stock page filter."""
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

    remaining = [c for c in categories_qs if c.id not in used_ids and c.nom not in category_hierarchy]
    if remaining:
        options.append({'value': '', 'label': 'Autres catégories', 'disabled': True})
        for category_obj in remaining:
            options.append({'value': str(category_obj.id), 'label': f'  - {category_obj.nom}', 'disabled': False})

    return options



#FOURNISSEUR
@login_required
@user_passes_test(lambda user: user.is_magasinier or user.is_directeur)
def create_fournisseur(request):
    employe = Employee.objects.get(user=request.user)
    nom = employe.nom
    prenom = employe.prenom
    page_temp = 'dashboard_directeur.html' if request.user.is_directeur else 'dashboard.html'
    # support search and pagination for the suppliers list
    q = request.GET.get('q', '').strip()
    suppliers_qs = Fournisseur.objects.all().order_by('nom')
    if q:
        # Search by name or category
        suppliers_qs = suppliers_qs.filter(
            models.Q(nom__icontains=q) | 
            models.Q(categories__nom__icontains=q)
        ).distinct()

    page_number = request.GET.get('page')
    paginator = Paginator(suppliers_qs, 8)
    suppliers = paginator.get_page(page_number)
    if request.method == 'POST':
        form = FournisseurForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fournisseur créé avec succès!')
            return redirect('transactions:create_fournisseur')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = FournisseurForm()

    return render(request, 'fournisseur_create.html', {
        'form': form,
        'nom': nom,
        'prenom': prenom,
        'page_temp': page_temp,
        'suppliers': suppliers,
        'q': q,
        'page_obj': suppliers,
        'categories': Categorie.objects.all(),
        'categories_json': list(Categorie.objects.all().values('id', 'nom')),
    })


@login_required
@user_passes_test(lambda user: user.is_magasinier)
def edit_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    employe = Employee.objects.get(user=request.user)
    nom = employe.nom
    prenom = employe.prenom
    page_temp = 'dashboard_directeur.html' if request.user.is_directeur else 'dashboard.html'

    # reuse search/pagination for the list on the edit page
    q = request.GET.get('q', '').strip()
    suppliers_qs = Fournisseur.objects.all().order_by('nom')
    if q:
        # Search by name or category
        suppliers_qs = suppliers_qs.filter(
            models.Q(nom__icontains=q) | 
            models.Q(categories__nom__icontains=q)
        ).distinct()
    paginator = Paginator(suppliers_qs, 8)
    page_number = request.GET.get('page')
    suppliers = paginator.get_page(page_number)

    if request.method == 'POST':
        form = FournisseurForm(request.POST, instance=fournisseur)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fournisseur mis à jour avec succès!')
            return redirect('transactions:create_fournisseur')
        else:
            messages.error(request, 'Veuillez corriger les erreurs du formulaire.')
    else:
        form = FournisseurForm(instance=fournisseur)

    return render(request, 'fournisseur_create.html', {
        'form': form,
        'nom': nom,
        'prenom': prenom,
        'page_temp': page_temp,
        'suppliers': suppliers,
        'q': q,
        'page_obj': suppliers,
        'categories': Categorie.objects.all(),
        'categories_json': list(Categorie.objects.all().values('id', 'nom')),
    })


@login_required
@user_passes_test(lambda user: user.is_magasinier)
@require_POST
def delete_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    try:
        fournisseur.delete()
        messages.success(request, 'Fournisseur supprimé.')
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


def _build_supply_request_mailto_urls(demande, employee_name):
    product_lines = [
        f"- {ligne.produit.libelle} ({ligne.produit.categorie.nom}) x {ligne.quantite}"
        for ligne in demande.lignes.select_related('produit').all()
    ]

    mailto_urls = []
    for fournisseur in demande.fournisseurs.all():
        if not fournisseur.email:
            continue

        body = '\n'.join([
            f"Bonjour {fournisseur.nom},",
            '',
            f"Une nouvelle demande d'approvisionnement a été préparée par {employee_name}.",
            f"Catégorie cible: {demande.categorie.nom}",
            f"Date de livraison souhaitée: {demande.date.strftime('%d/%m/%Y')}",
            '',
            'Produits demandés:',
            *product_lines,
            '',
            f"Message: {demande.message or 'Aucun message complémentaire.'}",
        ])
        mailto_urls.append({
            'name': fournisseur.nom,
            'email': fournisseur.email,
            'url': f"mailto:{fournisseur.email}?{urlencode({'subject': demande.objet, 'body': body}, quote_via=quote)}",
        })

    return mailto_urls


def _build_supply_request_mail_payload(demande, employee_name):
    mailto_urls = _build_supply_request_mailto_urls(demande, employee_name)
    return {
        'links': mailto_urls,
        'count': len(mailto_urls),
    }


@login_required
@user_passes_test(lambda user: user.is_directeur or user.is_magasinier)
def demande_fournisseur(request):
    employe = Employee.objects.filter(user=request.user).first()
    if employe.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
    else:
        page_temp = 'dashboard.html'

    nom = employe.nom
    prenom = employe.prenom

    # allow multiple categories selection (sent as categories[])
    selected_categories = request.POST.getlist('categories') or request.GET.getlist('categories')
    fournisseurs_qs = Fournisseur.objects.all().order_by('nom')

    if selected_categories:
        # Keep suppliers that match at least one selected category.
        # This preserves the previous UX where category filtering was inclusive.
        ids = [int(c) for c in selected_categories]
        fournisseurs_qs = fournisseurs_qs.filter(categories__id__in=ids).distinct()

    fournisseurs_qs = fournisseurs_qs.distinct().order_by('nom')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Get selected supplier IDs from the form to ensure they're included in the queryset
        selected_supplier_ids = [int(id) for id in request.POST.getlist('fournisseurs') if id.isdigit()]
        
        # Create a queryset that includes both filtered suppliers AND any selected suppliers
        # This prevents validation errors when category filtering changes between page load and submission
        if selected_supplier_ids:
            # Build a fresh queryset that includes all necessary suppliers to avoid distinct() conflicts
            form_fournisseurs_qs = Fournisseur.objects.filter(
                Q(id__in=selected_supplier_ids) |
                (Q(categories__id__in=selected_categories) if selected_categories else Q())
            ).distinct()
        else:
            form_fournisseurs_qs = fournisseurs_qs
        
        demande_form = DemandeApprovisionnementForm(
            request.POST,
            fournisseurs_queryset=form_fournisseurs_qs,
        )
        formset = DemandeApprovisionnementLigneFormSet(
            request.POST,
            instance=DemandeApprovisionnement(),
            prefix='lignes',
        )

        if demande_form.is_valid() and formset.is_valid():
            demande = demande_form.save(commit=False)
            # derive primary category from categories selection if provided
            selected_cats = demande_form.cleaned_data.get('categories') or []
            if selected_cats:
                demande.categorie = selected_cats[0]
            # default etat handling: saved but not sent
            if action == 'send':
                demande.etat = 'sent'
            else:
                demande.etat = 'created'

            demande.email_envoye = False
            demande.save()
            demande_form.save_m2m()
            formset.instance = demande
            formset.save()

            if action == 'send':
                mail_payload = _build_supply_request_mail_payload(
                    demande,
                    f'{nom} {prenom}',
                )
                if not mail_payload['links']:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'ok': False,
                            'error': 'Demande enregistrée, mais aucun fournisseur avec email valide n\'a été trouvé.'
                        })
                    messages.warning(request, 'Demande enregistrée, mais aucun fournisseur avec email valide n\'a été trouvé.')
                    return redirect('transactions:demande_fournisseur')

                demande.email_envoye = False
                demande.etat = 'sent'
                demande.save(update_fields=['email_envoye', 'etat'])
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'ok': True,
                        'message': 'Demande enregistrée. Mail Envoyée.',
                        'payload': mail_payload,
                    })
                
                messages.success(request, 'Demande enregistrée. Mail Envoyée.')
                mailto_links_html = ''.join(
                    f'<li class="mb-2"><a href="{item["url"]}" target="_blank" rel="noopener noreferrer" class="text-sky-700 underline">Ouvrir le mail pour {item["name"]} ({item["email"]})</a></li>'
                    for item in mail_payload['links']
                )
                mailto_urls_json = json.dumps([item['url'] for item in mail_payload['links']])
                html = (
                    '<!doctype html><html><head><meta charset="utf-8"><title>Open Mail Client</title>'
                    '<style>body{font-family:system-ui,sans-serif;padding:24px;color:#0f172a}a{display:inline-block;margin-top:8px}</style>'
                    '</head><body>'
                    '<p>Ouverture du client mail...</p>'
                    '<p>Si plusieurs fournisseurs ont été sélectionnés, chaque email s\'ouvre dans un nouvel onglet.</p>'
                    f'<ul>{mailto_links_html}</ul>'
                    f'<script>(function(){{var urls={mailto_urls_json};for(var i=0;i<urls.length;i++){{try{{window.open(urls[i],"_blank","noopener,noreferrer");}}catch(e){{}}}}}})();</script>'
                    '</body></html>'
                )
                return HttpResponse(html)

            # Handle save action
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': True,
                    'message': 'Demande enregistrée (brouillon).'
                })
            
            messages.success(request, 'Demande enregistrée (brouillon).')
            return redirect('transactions:demande_fournisseur')

        # Build detailed error messages
        error_messages = []
        
        # Check main form errors
        if not demande_form.is_valid():
            for field, errors in demande_form.errors.items():
                for error in errors:
                    if field == 'categories':
                        error_messages.append(f"Catégorie: {error}")
                    elif field == 'date':
                        error_messages.append(f"Date: {error}")
                    elif field == 'objet':
                        error_messages.append(f"Objet: {error}")
                    elif field == 'message':
                        error_messages.append(f"Message: {error}")
                    elif field == 'fournisseurs':
                        error_messages.append(f"Fournisseurs: {error}")
                    else:
                        error_messages.append(f"{field.title()}: {error}")
        
        # Check formset errors
        if not formset.is_valid():
            for i, form_errors in enumerate(formset.errors):
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            if field == 'produit':
                                error_messages.append(f"Ligne {i+1} - Produit: {error}")
                            elif field == 'quantite':
                                error_messages.append(f"Ligne {i+1} - Quantité: {error}")
                            elif field == 'id':
                                # Skip ID field validation - it's auto-generated
                                continue
                            else:
                                error_messages.append(f"Ligne {i+1} - {field.title()}: {error}")
            
            # Check non-form errors (like empty forms)
            if formset.non_form_errors():
                for error in formset.non_form_errors():
                    error_messages.append(f"Erreur globale: {error}")
        
        # Display specific error messages or fallback
        if error_messages:
            # Handle AJAX error responses
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': False,
                    'error': '; '.join(error_messages[:3])  # Send first 3 errors
                })
            for msg in error_messages[:5]:  # Limit to first 5 errors to avoid overwhelming
                messages.error(request, msg)
        else:
            # Handle AJAX error responses
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': False,
                    'error': 'Veuillez corriger les erreurs du formulaire.'
                })
            messages.error(request, 'Veuillez corriger les erreurs du formulaire.')
    else:
        initial = {
            'date': timezone.now().date().isoformat(),
        }
        # if categories were supplied via GET, set initial for the form's categories field
        if selected_categories:
            initial['categories'] = selected_categories

        demande_form = DemandeApprovisionnementForm(
            initial=initial,
            fournisseurs_queryset=fournisseurs_qs,
        )
        formset = DemandeApprovisionnementLigneFormSet(
            instance=DemandeApprovisionnement(),
            prefix='lignes',
        )

    categories_json = list(Categorie.objects.all().values('id', 'nom'))
    
    return render(
        request,
        'demande_fournisseur.html',
        {
            'demande_form': demande_form,
            'formset': formset,
            'fournisseurs': fournisseurs_qs,
            'categories': Categorie.objects.all(),
            'categories_json': categories_json,
            'debug_demande': {},
            'nom': nom,
            'prenom': prenom,
            'page_temp': page_temp,
        },
    )


@login_required
@user_passes_test(lambda user: user.is_directeur or user.is_magasinier)
def historique_fournisseurs(request):
    employe = Employee.objects.filter(user=request.user).first()
    if employe.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
    else:
        page_temp = 'dashboard.html'

    nom = employe.nom
    prenom = employe.prenom

    demandes = DemandeApprovisionnement.objects.select_related('categorie').prefetch_related(
        'fournisseurs',
        'lignes__produit',
    ).order_by('-date', '-pk')

    selected_categorie = request.GET.get('categorie', '')
    selected_email_envoye = request.GET.get('email_envoye', '')
    category_filter_options = _build_category_filter_options(Categorie.objects.all().order_by('nom'))

    if selected_categorie:
        demandes = demandes.filter(categorie_id=selected_categorie)
    if selected_email_envoye in {'0', '1'}:
        demandes = demandes.filter(email_envoye=selected_email_envoye == '1')

    paginator = Paginator(demandes, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'historique_fournisseurs.html',
        {
            'page_obj': page_obj,
            'categories': Categorie.objects.all(),
            'category_filter_options': category_filter_options,
            'selected_categorie': selected_categorie,
            'selected_email_envoye': selected_email_envoye,
            'nom': nom,
            'prenom': prenom,
            'page_temp': page_temp,
        },
    )


# API ENDPOINTS FOR AJAX
@login_required
@require_GET
def api_suppliers_by_category(request):
    """API endpoint to get suppliers filtered by category with transaction history."""
    category_ids = request.GET.get('category_ids') or request.GET.getlist('category_id')
    if not category_ids:
        return JsonResponse({'suppliers': []})

    # accept comma-separated or list
    if isinstance(category_ids, str) and ',' in category_ids:
        ids = [int(x) for x in category_ids.split(',') if x]
    elif isinstance(category_ids, str):
        ids = [int(category_ids)]
    else:
        ids = [int(x) for x in category_ids]

    suppliers = Fournisseur.objects.filter(categories__id__in=ids).distinct().annotate(
        transaction_count=Count('demandes_approvisionnement')
    ).values(
        'id', 'nom', 'email', 'transaction_count'
    ).order_by('nom')

    return JsonResponse({'suppliers': list(suppliers)})


@login_required
@require_GET
def api_products_by_category(request):
    """API endpoint to get products filtered by category."""
    category_ids = request.GET.get('category_ids') or request.GET.getlist('category_id')
    if not category_ids:
        return JsonResponse({'products': []})

    if isinstance(category_ids, str) and ',' in category_ids:
        ids = [int(x) for x in category_ids.split(',') if x]
    elif isinstance(category_ids, str):
        ids = [int(category_ids)]
    else:
        ids = [int(x) for x in category_ids]

    products = Produit.objects.filter(categorie_id__in=ids).values('id', 'libelle').order_by('libelle')

    return JsonResponse({'products': list(products)})


@login_required
@require_POST
def api_update_demande_state(request):
    """Update demande `etat` (created|sent|delivered). If delivered, increment stock quantities."""
    demande_id = request.POST.get('demande_id')
    new_state = request.POST.get('new_state')
    if not demande_id or not new_state:
        return JsonResponse({'ok': False, 'error': 'missing parameters'}, status=400)

    demande = get_object_or_404(DemandeApprovisionnement, pk=demande_id)

    if new_state not in {'created', 'sent', 'delivered'}:
        return JsonResponse({'ok': False, 'error': 'invalid state'}, status=400)

    # if marking delivered, increment product stock based on lines
    if new_state == 'delivered' and demande.etat != 'delivered':
        for line in demande.lignes.select_related('produit').all():
            p = line.produit
            p.quantite = (p.quantite or 0) + (line.quantite or 0)
            p.save(update_fields=['quantite'])

    demande.etat = new_state
    demande.save(update_fields=['etat'])
    return JsonResponse({'ok': True})


@login_required
@user_passes_test(lambda user: user.is_directeur or user.is_magasinier)
def edit_demande(request, pk):
    demande = get_object_or_404(DemandeApprovisionnement, pk=pk)
    employe = Employee.objects.filter(user=request.user).first()
    if employe.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
    else:
        page_temp = 'dashboard.html'

    # initial suppliers queryset based on existing demande.categorie
    fournisseurs_qs = Fournisseur.objects.filter(
        Q(categories__id=demande.categorie_id) | Q(pk__in=demande.fournisseurs.values_list('pk', flat=True))
    ).distinct()

    if request.method == 'POST':
        action = request.POST.get('action')
        post_data = request.POST.copy()
        if not post_data.getlist('categories') and demande.categorie_id:
            post_data.setlist('categories', [str(demande.categorie_id)])
        if not post_data.get('categorie') and demande.categorie_id:
            post_data['categorie'] = str(demande.categorie_id)

        posted_supplier_ids = [int(pk) for pk in post_data.getlist('fournisseurs') if pk.isdigit()]
        fournisseurs_qs = Fournisseur.objects.filter(
            Q(categories__id=demande.categorie_id)
            | Q(pk__in=demande.fournisseurs.values_list('pk', flat=True))
            | Q(pk__in=posted_supplier_ids)
        ).distinct()

        demande_form = DemandeApprovisionnementForm(post_data, instance=demande, fournisseurs_queryset=fournisseurs_qs)
        formset = DemandeApprovisionnementLigneFormSet(post_data, instance=demande, prefix='lignes')
        if demande_form.is_valid() and formset.is_valid():
            demande = demande_form.save(commit=False)
            # set primary category from categories field if provided
            selected_cats = demande_form.cleaned_data.get('categories') or []
            if selected_cats:
                demande.categorie = selected_cats[0]

            if action == 'send':
                demande.etat = 'sent'
            else:
                demande.etat = 'created'

            demande.save()
            demande_form.save_m2m()
            formset.save()

            if action == 'send':
                mail_payload = _build_supply_request_mail_payload(demande, f"{employe.nom} {employe.prenom}")
                if not mail_payload['links']:
                    messages.warning(request, 'Demande mise à jour, mais aucun fournisseur avec email valide n\'a été trouvé.')
                    return redirect('transactions:historique_fournisseurs')

                demande.email_envoye = False
                demande.etat = 'sent'
                demande.save(update_fields=['email_envoye', 'etat'])
                messages.success(request, 'Demande mise à jour. Ouverture du client mail.')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                    return JsonResponse({
                        'ok': True,
                        'message': 'Demande mise à jour. Ouverture du client mail.',
                        'payload': mail_payload,
                    })

                mailto_links_html = ''.join(
                    f'<li class="mb-2"><a href="{item["url"]}" target="_blank" rel="noopener noreferrer" class="text-sky-700 underline">Ouvrir le mail pour {item["name"]} ({item["email"]})</a></li>'
                    for item in mail_payload['links']
                )
                mailto_urls_json = json.dumps([item['url'] for item in mail_payload['links']])
                html = (
                    '<!doctype html><html><head><meta charset="utf-8"><title>Open Mail Client</title>'
                    '<style>body{font-family:system-ui,sans-serif;padding:24px;color:#0f172a}a{display:inline-block;margin-top:8px}</style>'
                    '</head><body>'
                    '<p>Ouverture du client mail...</p>'
                    '<p>Si plusieurs fournisseurs ont été sélectionnés, chaque email s\'ouvre dans un nouvel onglet.</p>'
                    f'<ul>{mailto_links_html}</ul>'
                    f'<script>(function(){{var urls={mailto_urls_json};for(var i=0;i<urls.length;i++){{try{{window.open(urls[i],"_blank","noopener,noreferrer");}}catch(e){{}}}}}})();</script>'
                    '</body></html>'
                )
                return HttpResponse(html)

            messages.success(request, 'Demande mise à jour.')
            return redirect('transactions:historique_fournisseurs')

        # Build detailed error messages
        error_messages = []
        
        # Check main form errors
        if not demande_form.is_valid():
            for field, errors in demande_form.errors.items():
                for error in errors:
                    if field == 'categories':
                        error_messages.append(f"Catégorie: {error}")
                    elif field == 'date':
                        error_messages.append(f"Date: {error}")
                    elif field == 'objet':
                        error_messages.append(f"Objet: {error}")
                    elif field == 'message':
                        error_messages.append(f"Message: {error}")
                    elif field == 'fournisseurs':
                        error_messages.append(f"Fournisseurs: {error}")
                    else:
                        error_messages.append(f"{field.title()}: {error}")
        
        # Check formset errors
        if not formset.is_valid():
            for i, form_errors in enumerate(formset.errors):
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            if field == 'produit':
                                error_messages.append(f"Ligne {i+1} - Produit: {error}")
                            elif field == 'quantite':
                                error_messages.append(f"Ligne {i+1} - Quantité: {error}")
                            elif field == 'id':
                                # Skip ID field validation - it's auto-generated
                                continue
                            else:
                                error_messages.append(f"Ligne {i+1} - {field.title()}: {error}")
            
            # Check non-form errors (like empty forms)
            if formset.non_form_errors():
                for error in formset.non_form_errors():
                    error_messages.append(f"Erreur globale: {error}")
        
        # Display specific error messages or fallback
        if error_messages:
            for msg in error_messages[:5]:  # Limit to first 5 errors to avoid overwhelming
                messages.error(request, msg)
        else:
            messages.error(request, 'Veuillez corriger les erreurs du formulaire.')
    else:
        # preserve the current date and categories when opening the edit form
        initial = {
            'date': demande.date.isoformat(),
            'categories': [demande.categorie_id],
        }
        demande_form = DemandeApprovisionnementForm(instance=demande, initial=initial, fournisseurs_queryset=fournisseurs_qs)
        # Use a formset with no extra blank form when editing to avoid the extra empty line
        from django.forms import inlineformset_factory
        from .forms import DemandeApprovisionnementLigneForm
        EditLigneFormSet = inlineformset_factory(
            DemandeApprovisionnement,
            DemandeApprovisionnementLigne,
            form=DemandeApprovisionnementLigneForm,
            fields=('produit', 'quantite'),
            extra=0,
            can_delete=False,
        )
        formset = EditLigneFormSet(instance=demande, prefix='lignes')

    # Debug info: expose what's actually stored on the demande for quick inspection
    try:
        debug_demande = {
            'id': demande.pk,
            'categorie_id': demande.categorie_id,
            'fournisseurs': list(demande.fournisseurs.values_list('id', flat=True)),
            'lignes': list(demande.lignes.values('produit_id', 'quantite')),
            'objet': demande.objet,
            'message': demande.message,
            'date': str(demande.date),
            'etat': demande.etat,
        }
        print("[DEBUG] edit_demande data:", debug_demande)
    except Exception as e:
        debug_demande = {'error': str(e)}
        print("[DEBUG] edit_demande error while building debug_demande:", e)

    return render(request, 'demande_fournisseur.html', {
        'demande_form': demande_form,
        'formset': formset,
        'fournisseurs': fournisseurs_qs,
        'categories': Categorie.objects.all(),
        'categories_json': list(Categorie.objects.all().values('id', 'nom')),
        'debug_demande': debug_demande,
        'nom': employe.nom,
        'prenom': employe.prenom,
        'page_temp': page_temp,
    })


@login_required
@require_POST
def delete_demande(request, pk):
    """Delete a DemandeApprovisionnement instance."""
    try:
        demande = get_object_or_404(DemandeApprovisionnement, pk=pk)
        demande.delete()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


#BULLETIN

@login_required
@user_passes_test(lambda user: user.is_directeur or user.is_magasinier or user.is_employee )
def new_bulletin(request):
    BulletinFormSet = inlineformset_factory(Bulletin_de_commande, DemandeDeProduit, fields=(
        'produit_demande', 'quantite_demande'), extra=0)
    employe = Employee.objects.filter(user=request.user).first()
    
    if employe.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
    elif employe.user.is_employee:
        page_temp = 'dashboard_employee.html'
    else:
        page_temp='dashboard.html'
     
    nom = employe.nom
    prenom = employe.prenom

    if request.method == 'POST':

        bulletin_form = BulletinForm(request.POST)
        
        formset = BulletinFormSet(
            request.POST, instance=bulletin_form.instance)
        if bulletin_form.is_valid() and formset.is_valid():
            bulletin = bulletin_form.save(commit=False)
            
            bulletin.state = Bulletin_de_commande.DEMANDER
            bulletin.save()

            formset.instance = bulletin
            formset.save()
            messages.success(request, 'Bulletin créé avec succès.')
            if employe.user.is_employee:
                return redirect('transactions:bulletin_list_employee')
            else:
                return redirect('transactions:bulletin_list')
        else:
            messages.error(request, 'Échec de la création du bulletin. Veuillez vérifier le formulaire et réessayer.')
    else:
        bulletin_form = BulletinForm(initial={'employe': employe})
        formset = BulletinFormSet(instance=Bulletin_de_commande())
    return render(request, 'new_bulletin.html', {'bulletin_form': bulletin_form, 'formset': formset, 'employe': employe, 'nom': nom, 'prenom': prenom,'page_temp':page_temp})




@login_required
@user_passes_test(lambda user: user.is_directeur or user.is_magasinier)
def bulletin_list(request):
    bulletins = Bulletin_de_commande.objects.exclude(state='supprimer').order_by('-date')
    employees = Employee.objects.all()
    employe = Employee.objects.get(user=request.user)
    if employe.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
    else:
        page_temp='dashboard.html'
    nom = employe.nom
    prenom = employe.prenom

    state_choices = [x[0]
                     for x in Bulletin_de_commande.STATE_CHOICES]

    selected_state = request.GET.get('state','')
    selected_employee = request.GET.get('employee', '')
    selected_date = request.GET.get('date', '')

    if selected_state:
        bulletins = bulletins.filter(state=selected_state).order_by('-date')
    if selected_employee:
        bulletins = bulletins.filter(employe=selected_employee).order_by('-date')
    if selected_date:
        bulletins = bulletins.filter(date=selected_date).order_by('-date')

    paginator = Paginator(bulletins, 8)
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'bulletin_list.html', {'page_obj': page_obj, 'state_choices': state_choices, 'employees': employees, 'nom': nom, 'prenom': prenom,'page_temp':page_temp,'selected_state':selected_state,'selected_employee':selected_employee,'selected_date':selected_date})

@login_required
@user_passes_test(lambda user: user.is_employee)
def bulletin_list_employee(request):
    employee = Employee.objects.get(user=request.user)
    bulletins = Bulletin_de_commande.objects.filter(employe=employee).order_by('-date')
    nom = employee.nom
    prenom = employee.prenom

    state_choices = [x[0].capitalize()
                     for x in Bulletin_de_commande.STATE_CHOICES]

    selected_state = request.GET.get('state','')
    selected_date = request.GET.get('date', '')

    if selected_state:
        bulletins = bulletins.filter(state=selected_state).order_by('-date')

    if selected_date:
        bulletins = bulletins.filter(date=selected_date).order_by('-date')

    paginator = Paginator(bulletins, 8)
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'bulletin_list_employee.html', {'page_obj': page_obj, 'state_choices': state_choices,  'nom': nom, 'prenom': prenom,'selected_state':selected_state,'selected_date':selected_date})


@login_required
@user_passes_test(lambda user: user.is_directeur or user.is_magasinier)
def bulletin_detail(request, pk):
    bulletin = Bulletin_de_commande.objects.get(pk=pk)
    employe = Employee.objects.get(user=request.user)
    if employe.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
        trait = 'transactions:modify_bulletin'
    else:
        page_temp='dashboard.html'
        trait = 'transactions:traiter_bulletin'


     
    nom = employe.nom
    prenom = employe.prenom

    context = {
        'bulletin': bulletin,
        'nom': nom,
        'prenom': prenom,
        'page_temp':page_temp,
        'trait':trait
    }
    return render(request, 'bulletin_detail.html', context)


@login_required
@user_passes_test(lambda user: user.is_directeur or user.is_magasinier)
def voir_bulletin(request, pk):
    bulletin = Bulletin_de_commande.objects.get(pk=pk)
    employe = Employee.objects.get(user=request.user)
    if employe.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
    else:
        page_temp='dashboard.html'
     
    nom = employe.nom
    prenom = employe.prenom

    context = {
        'bulletin': bulletin,
        'nom': nom,
        'prenom': prenom,
        'page_temp':page_temp }
    return render(request, 'voir_bulletin.html', context)


@login_required
@user_passes_test(lambda user: user.is_employee)
def voir_bulletin_employee(request, pk):
    bulletin = Bulletin_de_commande.objects.get(pk=pk)
    employe = Employee.objects.get(user=request.user)
    nom = employe.nom
    prenom = employe.prenom

    context = {
        'bulletin': bulletin,
        'nom': nom,
        'prenom': prenom,
         }
    return render(request, 'voir_bulletin_employe.html', context)


@login_required
@user_passes_test(lambda user: user.is_directeur or user.is_magasinier or user.is_employee)
def supprimer_bulletin(request, pk):
    bulletin = get_object_or_404(Bulletin_de_commande, pk=pk)
    bulletin.state = Bulletin_de_commande.SUPPRIMER
    employe = Employee.objects.get(user=request.user)


    bulletin.save()
    messages.success(request, 'Le bulletin a été supprimé avec succès.')
    if employe.user.is_employee:
        return redirect('transactions:bulletin_list_employee')
    else:
        return redirect('transactions:bulletin_list')




@login_required
@user_passes_test(lambda user: user.is_directeur)
@require_POST
def modify_bulletin(request, bulletin_id):
    bulletin = get_object_or_404(Bulletin_de_commande, pk=bulletin_id)
    demandes = bulletin.demandedeproduit_set.all()

    for demande in demandes:
        quantite_fournie = request.POST.get(
            'quantite_fournie_{}'.format(demande.pk))

        if quantite_fournie is not None:
            try:
                quantite_fournie = int(quantite_fournie)
            except ValueError:
                messages.error(
                    request, 'La quantité fournie doit être un nombre entier')
                return redirect('transactions:bulletin_detail', pk=bulletin.pk)

            if quantite_fournie < 0:
                messages.error(
                    request, 'La quantité fournie doit être positive')
                return redirect('transactions:bulletin_detail', pk=bulletin.pk)

            if quantite_fournie > demande.produit_demande.quantite and quantite_fournie != 0:
                messages.error(request, 'La quantité fournie est supérieure à la quantité en stock pour {}'.format(
                    demande.produit_demande.libelle))
                return redirect('transactions:bulletin_detail', pk=bulletin.pk)

            demande.quantite_fournie = quantite_fournie
            demande.save()

           

    bulletin.state = Bulletin_de_commande.APPROVER
    bulletin.save()
    messages.success(
        request, 'Bulletin Approver')
    return redirect('transactions:bulletin_list')


@login_required
@user_passes_test(lambda user:user.is_magasinier)
@require_POST
def traiter_bulletin(request, bulletin_id):
    bulletin = get_object_or_404(Bulletin_de_commande, pk=bulletin_id)
    demandes = bulletin.demandedeproduit_set.all()

    for demande in demandes:
        quantite_fournie = request.POST.get(
            'quantite_fournie_{}'.format(demande.pk))

        if quantite_fournie is not None:
            try:
                quantite_fournie = int(quantite_fournie)
            except ValueError:
                messages.error(
                    request, 'La quantité fournie doit être un nombre entier')
                return redirect('transactions:bulletin_detail', pk=bulletin.pk)

            if quantite_fournie < 0:
                messages.error(
                    request, 'La quantité fournie doit être positive')
                return redirect('transactions:bulletin_detail', pk=bulletin.pk)

            if quantite_fournie > demande.produit_demande.quantite and quantite_fournie != 0:
                messages.error(request, 'La quantité fournie est supérieure à la quantité en stock pour {}'.format(
                    demande.produit_demande.libelle))
                return redirect('transactions:bulletin_detail', pk=bulletin.pk)
            demande.quantite_fournie = quantite_fournie
            demande.save()

            produit = demande.produit_demande
            produit.quantite -= quantite_fournie
            produit.save()
    bulletin.state = Bulletin_de_commande.TRAITER
    bulletin.save()
    messages.success(
        request, 'Bulletin Traiter')
    return redirect('transactions:bulletin_list')


# SORTIE
@login_required
@user_passes_test(lambda user: user.is_magasinier)
def bon_list(request):
    bon = Bonne_livraison.objects.all()
    employe = Employee.objects.get(user=request.user)
    nom = employe.nom
    prenom = employe.prenom
    paginator = Paginator(bon, 8)

    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page_obj = paginator.get_page(page_number)

    return render(request, 'bon_list.html', {'page_obj': page_obj, 'nom': nom, 'prenom': prenom})


@login_required
@user_passes_test(lambda user: user.is_magasinier)
def voir_bon(request, pk):
    livraison = Bonne_livraison.objects.get(pk=pk)
    employe = Employee.objects.get(user=request.user)
    nom = employe.nom
    prenom = employe.prenom
    context = {
        'bl': livraison,
        'nom': nom,
        'prenom': prenom
    }
    return render(request, 'voir_bon.html', context)


@login_required
@user_passes_test(lambda user: user.is_magasinier)
def new_bon(request):
    employe = Employee.objects.get(user=request.user)
    nom = employe.nom
    prenom = employe.prenom
    if request.method == 'POST':
        # Create the BonForm instance with the POST data
        bon_form = BonForm(request.POST)
        # Create the EntreeDeProduitFormSet instance with the POST data and the Bonne_livraison instance from the BonForm
        formset = EntreeDeProduitFormSet(
            request.POST, instance=bon_form.instance)

        # Check that both forms are valid
        if bon_form.is_valid() and formset.is_valid():
            # Save the Bonne_livraison instance
            bon = bon_form.save(commit=False)
            bon.save()
            formset.instance = bon
            formset.save()

            # Updatethe quantite field of each product in the Bonne_livraison
            for entree in bon.entreedeproduit_set.all():
                if entree.produit_entree != "" or entree.quantite_entree != "":
                    produit = entree.produit_entree
                    produit.quantite += entree.quantite_entree
                    produit.save()
                else:
                     messages.error(request, 'Veuillez remplir les valeurs necessaire')
                     redirect('transactions:new_bon')
                messages.success(request, 'Nouveau bon de livraison est crée!')
                    
            return redirect('transactions:bon_list')
        else:
            messages.error(request, 'Le formulaire contient des erreurs. Veuillez le corriger.')
    else:
        # Create new instances of the BonForm and EntreeDeProduitFormSet
        bon_form = BonForm()
        formset = EntreeDeProduitFormSet(instance=Bonne_livraison())

    # Render the new_bon template with the BonForm and EntreeDeProduitFormSet instances
    return render(request, 'new_bon.html', {'bon_form': bon_form, 'formset': formset, 'nom': nom, 'prenom': prenom})


#### RAPPORT ######
from produit.models import Categorie

@login_required
@user_passes_test(lambda user: user.is_magasinier or user.is_directeur)
def date_range(request):
    employee = Employee.objects.get(user=request.user)
    
    if employee.user.is_directeur:
        page_temp = 'dashboard_directeur.html'
    else:
        page_temp='dashboard.html'
    categories = Categorie.objects.all()
    category_filter_options = _build_category_filter_options(categories.order_by('nom'))

    nom = employee.nom
    prenom = employee.prenom
    selected_categories = []
    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        selected_categories = request.POST.getlist('categories')
        if form.is_valid():

            date_debut = form.cleaned_data['date_debut']
            date_fin = form.cleaned_data['date_fin']
            bulletins = Bulletin_de_commande.objects.filter(
                date__range=[date_debut, date_fin])

            products = Produit.objects.filter(
                demandedeproduit__bulletin__in=bulletins)
            category_ids = selected_categories
            if category_ids:
                products = products.filter(categorie__id__in=category_ids)
            quantities = products.annotate(total_quantity=Sum(
                'demandedeproduit__quantite_fournie'))
            form = DateRangeForm()
            return render(request, 'date_range.html', {'quantities': quantities, 'form': form, 'date_debut': date_debut, 'date_fin': date_fin, 'nom': nom, 'prenom': prenom,'page_temp':page_temp ,'categories':categories,'category_filter_options': category_filter_options,'selected_categories': selected_categories})
    else:
        form = DateRangeForm()
    return render(request, 'date_range.html', {'form': form, 'nom': nom, 'prenom': prenom, 'page_temp':page_temp,'categories':categories,'category_filter_options': category_filter_options,'selected_categories': selected_categories})
