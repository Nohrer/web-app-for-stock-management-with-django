from decimal import Decimal
from datetime import date, datetime, timedelta
import random

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

            # Keep a few legacy categories to preserve existing sample records.
            legacy_categories = [
                ('Electronique', 'Produits et accessoires electroniques'),
                ('Alimentation', 'Produits alimentaires et consommables'),
                ('Bureau', 'Fournitures de bureau'),
                ('Informatique', 'Materiel informatique et reseau'),
            ]

            # Create main categories first (without parents)
            categories = {}
            for head_name, sub_names in category_hierarchy.items():
                # Create main category
                main_cat, _ = Categorie.objects.get_or_create(
                    nom=head_name,
                    defaults={'description': f'Head category: {head_name}', 'magasin': magasin, 'parent': None},
                )
                if main_cat.description != f'Head category: {head_name}' or main_cat.magasin_id != magasin.id:
                    main_cat.description = f'Head category: {head_name}'
                    main_cat.magasin = magasin
                    main_cat.parent = None
                    main_cat.save(update_fields=['description', 'magasin', 'parent'])
                categories[head_name] = main_cat
                
                # Create subcategories with parent set to main category
                for sub_name in sub_names:
                    sub_cat, _ = Categorie.objects.get_or_create(
                        nom=sub_name,
                        defaults={'description': f'Sub category under {head_name}', 'magasin': magasin, 'parent': main_cat},
                    )
                    if sub_cat.description != f'Sub category under {head_name}' or sub_cat.magasin_id != magasin.id or sub_cat.parent_id != main_cat.id:
                        sub_cat.description = f'Sub category under {head_name}'
                        sub_cat.magasin = magasin
                        sub_cat.parent = main_cat
                        sub_cat.save(update_fields=['description', 'magasin', 'parent'])
                    categories[sub_name] = sub_cat
            
            # Create legacy categories (without parents)
            for name, description in legacy_categories:
                categorie, _ = Categorie.objects.get_or_create(
                    nom=name,
                    defaults={'description': description, 'magasin': magasin, 'parent': None},
                )
                if categorie.description != description or categorie.magasin_id != magasin.id:
                    categorie.description = description
                    categorie.magasin = magasin
                    categorie.parent = None
                    categorie.save(update_fields=['description', 'magasin', 'parent'])
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

            # Requested volume: two products for each sub-category.
            all_sub_categories = [sub for subs in category_hierarchy.values() for sub in subs]
            for idx, sub_name in enumerate(all_sub_categories, start=1):
                for prod_idx in range(1, 3):
                    product_specs.append(
                        (
                            categories[sub_name],
                            f'{sub_name} - Produit {prod_idx}',
                            f'SUB{idx:03d}-P{prod_idx}',
                            20 + (prod_idx * 5),
                            f'Produit demo {prod_idx} pour la sous-categorie {sub_name}',
                        )
                    )

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
                    'note': 'Partenaire historique pour les achats techniques',
                },
                {
                    'nom': 'Food Market Pro',
                    'adresse': '88 Zone Industrielle',
                    'telephone': '0622334455',
                    'email': 'food.market@example.com',
                    'categories': ['Alimentation'],
                    'note': 'Livraisons rapides pour les denrees et consommables',
                },
                {
                    'nom': 'Bureau Plus',
                    'adresse': '5 Rue des Services',
                    'telephone': '0633445566',
                    'email': 'bureau.plus@example.com',
                    'categories': ['Bureau'],
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
                        'note': spec['note'],
                    },
                )
                fournisseur.adresse = spec['adresse']
                fournisseur.telephone = spec['telephone']
                fournisseur.email = spec['email']
                fournisseur.note = spec['note']
                fournisseur.save()
                fournisseur.categories.set([categories[name] for name in spec['categories']])
                suppliers[spec['nom']] = fournisseur

            # Requested volume: two suppliers for each pair of sub-categories.
            for pair_index in range(0, len(all_sub_categories), 2):
                pair_number = (pair_index // 2) + 1
                pair_categories = all_sub_categories[pair_index:pair_index + 2]

                for supplier_idx in range(1, 3):
                    supplier_name = f'Demo Pair Supplier {pair_number:02d}-{supplier_idx}'
                    supplier_phone = f'07{pair_number:02d}{supplier_idx}45678'
                    supplier_email = f'demo.pair.{pair_number:02d}.{supplier_idx}@example.com'

                    fournisseur, _ = Fournisseur.objects.get_or_create(
                        nom=supplier_name,
                        defaults={
                            'adresse': f'Zone industrielle lot {pair_number:02d}-{supplier_idx}',
                            'telephone': supplier_phone,
                            'email': supplier_email,
                            'note': f'Fournisseur demo rattache aux sous-categories: {", ".join(pair_categories)}',
                        },
                    )
                    fournisseur.adresse = f'Zone industrielle lot {pair_number:02d}-{supplier_idx}'
                    fournisseur.telephone = supplier_phone
                    fournisseur.email = supplier_email
                    fournisseur.note = f'Fournisseur demo rattache aux sous-categories: {", ".join(pair_categories)}'
                    fournisseur.save()
                    fournisseur.categories.set([categories[name] for name in pair_categories])
                    suppliers[supplier_name] = fournisseur

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

            # Get or create a demo bulletin - use first() if multiple exist
            bulletin = Bulletin_de_commande.objects.filter(
                employe=employees['employee_demo'],
                state=Bulletin_de_commande.DEMANDER
            ).first()
            if not bulletin:
                bulletin = Bulletin_de_commande.objects.create(
                    employe=employees['employee_demo'],
                    state=Bulletin_de_commande.DEMANDER,
                )
            if not bulletin.demandedeproduit_set.exists():
                DemandeDeProduit.objects.create(bulletin=bulletin, produit_demande=products['ELEC-001'], quantite_demande=5)
                DemandeDeProduit.objects.create(bulletin=bulletin, produit_demande=products['BUREAU-001'], quantite_demande=12)

            today = date.today()
            
            livraison, created = Bonne_livraison.objects.get_or_create(
                date=today,
                fournisseur=suppliers['Tech Distrib'],
                type_bl=type_livraison,
            )
            if created or not livraison.entreedeproduit_set.exists():
                EntreeDeProduit.objects.create(bl=livraison, produit_entree=products['INFO-001'], quantite_entree=10)
                EntreeDeProduit.objects.create(bl=livraison, produit_entree=products['INFO-002'], quantite_entree=15)

            demande, created = DemandeApprovisionnement.objects.get_or_create(
                objet='Demande initiale approvisionnement electronique',
                defaults={
                    'date': today,
                    'categorie': categories['Electronique'],
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

            # Ensure there are up to 50 demo bulletins with random products and states.
            # The creation is idempotent: only create missing bulletins up to the target.
            TARGET_BULLETIN_COUNT = 50
            existing_bulletins = Bulletin_de_commande.objects.count()
            to_create = max(0, TARGET_BULLETIN_COUNT - existing_bulletins)
            product_list = list(products.values())
            employee_list = list(employees.values())
            state_choices = [s[0] for s in Bulletin_de_commande.STATE_CHOICES]

            for i in range(to_create):
                employe = random.choice(employee_list)
                state = random.choice(state_choices)
                # Random date within last 30 days for variety
                days_ago = random.randint(0, 30)
                rand_date = today - timedelta(days=days_ago)
                b = Bulletin_de_commande.objects.create(
                    employe=employe,
                    state=state,
                    date=rand_date,
                )
                # Add 1-5 random demande de produit lines
                for _ in range(random.randint(1, 5)):
                    prod = random.choice(product_list)
                    qty = random.randint(1, 50)
                    DemandeDeProduit.objects.create(
                        bulletin=b,
                        produit_demande=prod,
                        quantite_demande=qty,
                    )

            self.stdout.write(self.style.SUCCESS('Demo data seeded successfully.'))