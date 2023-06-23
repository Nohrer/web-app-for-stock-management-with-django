from django.urls import reverse
from django.template.loader import get_template
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Bulletin_de_commande, DemandeDeProduit, Bonne_livraison, EntreeDeProduit
from django.forms import inlineformset_factory
from django.views.decorators.http import require_POST
from django.contrib import messages
from produit.models import Produit
from users.models import Employee
from django.db.models import Q
from .forms import BulletinForm, EntreeDeProduitFormSet, BonForm, DateRangeForm,FournisseurForm
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required,user_passes_test
from django.core.paginator import Paginator
from django.db.models import Sum



#FOURNISSEUR
@login_required
@user_passes_test(lambda user: user.is_magasinier)
def create_fournisseur(request):
    employe = Employee.objects.get(user=request.user)
    nom = employe.nom
    prenom = employe.prenom 
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
    return render(request, 'fournisseur_create.html', {'form': form,'nom':nom,'prenom':prenom})
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

    nom = employee.nom
    prenom = employee.prenom
    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        if form.is_valid():

            date_debut = form.cleaned_data['date_debut']
            date_fin = form.cleaned_data['date_fin']
            bulletins = Bulletin_de_commande.objects.filter(
                date__range=[date_debut, date_fin])

            products = Produit.objects.filter(
                demandedeproduit__bulletin__in=bulletins)
            category_ids = request.POST.getlist('categories')
            if category_ids:
                products = products.filter(categorie__id__in=category_ids)
            quantities = products.annotate(total_quantity=Sum(
                'demandedeproduit__quantite_fournie'))
            form = DateRangeForm()
            return render(request, 'date_range.html', {'quantities': quantities, 'form': form, 'date_debut': date_debut, 'date_fin': date_fin, 'nom': nom, 'prenom': prenom,'page_temp':page_temp ,'categories':categories})
    else:
        form = DateRangeForm()
    return render(request, 'date_range.html', {'form': form, 'nom': nom, 'prenom': prenom, 'page_temp':page_temp,'categories':categories})
