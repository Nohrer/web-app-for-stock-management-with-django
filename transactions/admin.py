from django.contrib import admin
from .models import Fournisseur,  Bulletin_de_commande, DemandeDeProduit, EntreeDeProduit, Bonne_livraison, type_bl

admin.site.register(Fournisseur)
admin.site.register(type_bl)


class DemandeDeProduitInline(admin.TabularInline):
    model = DemandeDeProduit
    extra = 1


@admin.register(Bulletin_de_commande)
class BulletinAdmin(admin.ModelAdmin):
    inlines = [DemandeDeProduitInline]


class EntreeProduittInline(admin.TabularInline):
    model = EntreeDeProduit
    extra = 1


@admin.register(Bonne_livraison)
class EntreeAdmin(admin.ModelAdmin):
    inlines = [EntreeProduittInline]
