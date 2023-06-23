
from django.urls import path
from .views import product_list, search_product, ajouter, product_state
app_name = 'produit'


urlpatterns = [
    path('produit/', product_list, name='product_list'),
    path('produit/search/', search_product, name='search_product'),
    path('ajouter/', ajouter, name='ajouter'),
    path('etat_stock/', product_state, name='product_state'),


]
