from django.contrib import admin
from .models import Magasin, Categorie, Produit
from import_export.admin import ImportExportModelAdmin
# Register your models here.
admin.site.register(Magasin)
admin.site.register(Categorie)
# admin.site.register(Produit)
@admin.register(Produit)
class userdata(ImportExportModelAdmin):
    pass