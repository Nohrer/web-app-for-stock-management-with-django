from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_demandeapprovisionnement_expand_fournisseur'),
    ]

    operations = [
        migrations.AddField(
            model_name='demandeapprovisionnement',
            name='etat',
            field=models.CharField(choices=[('created', 'Cr\u00e9e\u00e9'), ('sent', 'Envoy\u00e9e'), ('delivered', 'Livr\u00e9e')], default='created', max_length=20),
            preserve_default=False,
        ),
    ]
