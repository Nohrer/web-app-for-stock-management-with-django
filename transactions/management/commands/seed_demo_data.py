from decimal import Decimal
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from produit.models import Magasin, Categorie, Produit
from transactions.models import (
    Fournisseur,
    type_bl,
    Bulletin_de_commande,
    DemandeDeProduit,
    Bonne_livraison,
    EntreeDeProduit,
    DemandeApprovisionnement,
)
from users.models import User, Service, Employee


class Command(BaseCommand):
    help = 'Seed demo data for the stock management app.'

    def handle(self, *args, **options):
        with transaction.atomic():
            magasin = Magasin.objects.first()
            if magasin is None:
                magasin = Magasin.objects.create()

            services = {}
            for service_name in ['Direction', 'Magasin', 'Achats']:
                service, _ = Service.objects.get_or_create(nom=service_name)
                services[service_name] = service

            category_specs = [
                ('Electronique', 'Produits et accessoires electroniques'),
                ('Alimentation', 'Produits alimentaires et consommables'),
                ('Bureau', 'Fournitures de bureau'),
                ('Informatique', 'Materiel informatique et reseau'),
            ]
            categories = {}
            for name, description in category_specs:
                categorie, _ = Categorie.objects.get_or_create(
                    nom=name,
                    defaults={'description': description, 'magasin': magasin},
                )
                if categorie.description != description or categorie.magasin_id != magasin.id:
                    categorie.description = description
                    categorie.magasin = magasin
                    categorie.save(update_fields=['description', 'magasin'])
                categories[name] = categorie

            product_specs = [
                (categories['Electronique'], 'Ecran 24 pouces', 'ELEC-001', 18, 'Ecran full HD pour postes de travail'),
                (categories['Electronique'], 'Souris sans fil', 'ELEC-002', 60, 'Souris optique sans fil'),
                (categories['Alimentation'], 'Cafes en grains', 'FOOD-001', 120, 'Paquet 1kg'),
                (categories['Alimentation'], 'Eau minerale', 'FOOD-002', 250, 'Bouteille 1.5L'),
                (categories['Bureau'], 'Ramettes A4', 'BUREAU-001', 75, 'Ramette de 500 feuilles'),
                (categories['Bureau'], 'Stylos bleus', 'BUREAU-002', 300, 'Boite de 50 stylos'),
                (categories['Informatique'], 'Cable reseau', 'INFO-001', 90, 'Cable RJ45 5m'),
                (categories['Informatique'], 'Clavier USB', 'INFO-002', 40, 'Clavier standard USB'),
            ]
            products = {}
            for categorie, libelle, reference, quantite, detaille in product_specs:
                produit, _ = Produit.objects.get_or_create(
                    reference=reference,
                    defaults={
                        'categorie': categorie,
                        'libelle': libelle,
                        'quantite': quantite,
                        'detaille': detaille,
                    },
                )
                updates = []
                if produit.categorie_id != categorie.id:
                    produit.categorie = categorie
                    updates.append('categorie')
                if produit.libelle != libelle:
                    produit.libelle = libelle
                    updates.append('libelle')
                if produit.quantite != quantite:
                    produit.quantite = quantite
                    updates.append('quantite')
                if (produit.detaille or '') != detaille:
                    produit.detaille = detaille
                    updates.append('detaille')
                if updates:
                    produit.save(update_fields=updates)
                products[reference] = produit

            supplier_specs = [
                {
                    'nom': 'Tech Distrib',
                    'adresse': '12 Avenue de la Cooperation',
                    'telephone': '0612345678',
                    'email': 'tech.distrib@example.com',
                    'categories': ['Electronique', 'Informatique'],
                    'delai_livraison_jours': 3,
                    'prix_reference': Decimal('1200.00'),
                    'note': 'Partenaire historique pour les achats techniques',
                },
                {
                    'nom': 'Food Market Pro',
                    'adresse': '88 Zone Industrielle',
                    'telephone': '0622334455',
                    'email': 'food.market@example.com',
                    'categories': ['Alimentation'],
                    'delai_livraison_jours': 2,
                    'prix_reference': Decimal('450.00'),
                    'note': 'Livraisons rapides pour les denrees et consommables',
                },
                {
                    'nom': 'Bureau Plus',
                    'adresse': '5 Rue des Services',
                    'telephone': '0633445566',
                    'email': 'bureau.plus@example.com',
                    'categories': ['Bureau'],
                    'delai_livraison_jours': 4,
                    'prix_reference': Decimal('380.00'),
                    'note': 'Fournisseur de reference pour les achats de bureau',
                },
            ]
            suppliers = {}
            for spec in supplier_specs:
                fournisseur, _ = Fournisseur.objects.get_or_create(
                    nom=spec['nom'],
                    defaults={
                        'adresse': spec['adresse'],
                        'telephone': spec['telephone'],
                        'email': spec['email'],
                        'delai_livraison_jours': spec['delai_livraison_jours'],
                        'prix_reference': spec['prix_reference'],
                        'note': spec['note'],
                    },
                )
                fournisseur.adresse = spec['adresse']
                fournisseur.telephone = spec['telephone']
                fournisseur.email = spec['email']
                fournisseur.delai_livraison_jours = spec['delai_livraison_jours']
                fournisseur.prix_reference = spec['prix_reference']
                fournisseur.note = spec['note']
                fournisseur.save()
                fournisseur.categories.set([categories[name] for name in spec['categories']])
                suppliers[spec['nom']] = fournisseur

            type_livraison, _ = type_bl.objects.get_or_create(typpe='Livraison standard')
            type_bl.objects.get_or_create(typpe='Reception fournisseur')

            demo_users = [
                ('admin_demo', 'Demo12345!', False, False, False, 'Admin', 'Demo', 'ADM-001', services['Direction']),
                ('directeur_demo', 'Demo12345!', True, False, False, 'Directeur', 'Demo', 'DIR-001', services['Direction']),
                ('magasinier_demo', 'Demo12345!', False, True, False, 'Magasinier', 'Demo', 'MAG-001', services['Magasin']),
                ('employee_demo', 'Demo12345!', False, False, True, 'Employee', 'Demo', 'EMP-001', services['Achats']),
            ]
            employees = {}
            for username, password, is_directeur, is_magasinier, is_employee, nom, prenom, matricule, service in demo_users:
                user, created = User.objects.get_or_create(username=username, defaults={
                    'is_directeur': is_directeur,
                    'is_magasinier': is_magasinier,
                    'is_employee': is_employee,
                })
                if created or not user.check_password(password):
                    user.set_password(password)
                user.is_directeur = is_directeur
                user.is_magasinier = is_magasinier
                user.is_employee = is_employee
                user.is_staff = username == 'admin_demo'
                user.is_superuser = username == 'admin_demo'
                user.save()
                if username != 'admin_demo':
                    employee, _ = Employee.objects.update_or_create(
                        user=user,
                        defaults={
                            'nom': nom,
                            'prenom': prenom,
                            'matricule': matricule,
                            'service': service,
                        },
                    )
                    employees[username] = employee

            bulletin, created = Bulletin_de_commande.objects.get_or_create(
                employe=employees['employee_demo'],
                defaults={'state': Bulletin_de_commande.DEMANDER},
            )
            if created or not bulletin.demandedeproduit_set.exists():
                bulletin.state = Bulletin_de_commande.DEMANDER
                bulletin.save(update_fields=['state'])
                DemandeDeProduit.objects.create(bulletin=bulletin, produit_demande=products['ELEC-001'], quantite_demande=5)
                DemandeDeProduit.objects.create(bulletin=bulletin, produit_demande=products['BUREAU-001'], quantite_demande=12)

            livraison, created = Bonne_livraison.objects.get_or_create(
                date=date(2026, 5, 6),
                fournisseur=suppliers['Tech Distrib'],
                type_bl=type_livraison,
            )
            if created or not livraison.entreedeproduit_set.exists():
                EntreeDeProduit.objects.create(bl=livraison, produit_entree=products['INFO-001'], quantite_entree=10)
                EntreeDeProduit.objects.create(bl=livraison, produit_entree=products['INFO-002'], quantite_entree=15)

            demande, created = DemandeApprovisionnement.objects.get_or_create(
                objet='Demande initiale approvisionnement electronique',
                defaults={
                    'date': date(2026, 5, 6),
                    'categorie': categories['Electronique'],
                    'delai_max_jours': 5,
                    'prix_max': Decimal('1500.00'),
                    'message': 'Demande de reference pour les achats technologiques.',
                    'email_envoye': True,
                },
            )
            if created or not demande.lignes.exists():
                demande.lignes.create(produit=products['ELEC-001'], quantite=4)
                demande.lignes.create(produit=products['INFO-002'], quantite=8)
            if created or not demande.fournisseurs.exists():
                demande.fournisseurs.set([suppliers['Tech Distrib']])
            demande.email_envoye = True
            demande.save(update_fields=['email_envoye'])

            self.stdout.write(self.style.SUCCESS('Demo data seeded successfully.'))