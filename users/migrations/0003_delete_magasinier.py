# Generated by Django 4.2.1 on 2023-06-19 12:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_is_directeur_alter_user_is_magasinier'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Magasinier',
        ),
    ]
