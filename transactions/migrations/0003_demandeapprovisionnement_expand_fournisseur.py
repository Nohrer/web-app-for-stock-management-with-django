from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('produit', '0002_initial'),
        ('transactions', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fournisseur',
            name='categories',
            field=models.ManyToManyField(blank=True, related_name='fournisseurs', to='produit.categorie'),
        ),
        migrations.AddField(
            model_name='fournisseur',
            name='delai_livraison_jours',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='fournisseur',
            name='email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='fournisseur',
            name='note',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='fournisseur',
            name='prix_reference',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.CreateModel(
            name='DemandeApprovisionnement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('delai_max_jours', models.PositiveIntegerField(blank=True, null=True)),
                ('prix_max', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('objet', models.CharField(max_length=200)),
                ('message', models.TextField(blank=True)),
                ('email_envoye', models.BooleanField(default=False)),
                ('categorie', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='produit.categorie')),
                ('fournisseurs', models.ManyToManyField(blank=True, related_name='demandes_approvisionnement', to='transactions.fournisseur')),
            ],
        ),
        migrations.CreateModel(
            name='DemandeApprovisionnementLigne',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantite', models.PositiveIntegerField()),
                ('demande', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes', to='transactions.demandeapprovisionnement')),
                ('produit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='produit.produit')),
            ],
        ),
    ]