
from django.urls import path
from .views import new_bulletin, bulletin_list, bulletin_detail, modify_bulletin, voir_bulletin, bon_list, voir_bon, new_bon, date_range, supprimer_bulletin,traiter_bulletin,create_fournisseur,bulletin_list_employee,voir_bulletin_employee,demande_fournisseur,historique_fournisseurs,api_suppliers_by_category,api_products_by_category,api_update_demande_state, edit_demande, delete_demande


app_name = 'transactions'

urlpatterns = [
    # BULLETIN RELATED

    path('bulletin_new/', new_bulletin, name='new_bulletin'),
    path('bulletin_detail/<int:pk>/',
         bulletin_detail, name='bulletin_detail'),
     path('bulletin_detail/<int:pk>/',
         bulletin_detail, name='bulletin_detail'),
    path('bulletin/<int:pk>/',
         voir_bulletin, name='voir_bulletin'),
     path('mon_bulletin/<int:pk>/',
         voir_bulletin_employee, name='voir_bulletin_employee'),
    path('bulletin/<int:pk>/supprimer/',
         supprimer_bulletin, name='supprimer_bulletin'),

    path('bulletin/', bulletin_list, name='bulletin_list'),
    path('mes_bulletin/', bulletin_list_employee, name='bulletin_list_employee'),
    path('bulletin/<int:bulletin_id>/modify/',
         modify_bulletin, name='modify_bulletin'),
     path('bulletin/<int:bulletin_id>/traiter/',
         traiter_bulletin, name='traiter_bulletin'),

    # ENTREE DE PRODUIT

    path('bonne_livraion/', bon_list, name='bon_list'),
    path('bonn_new/', new_bon, name='new_bon'),


    path('bon/<int:pk>/',
         voir_bon, name='voir_bon'),

     path('ajout_fournisseur',create_fournisseur,name='create_fournisseur'),
    path('demande_fournisseur/', demande_fournisseur, name='demande_fournisseur'),
    path('demande_fournisseur/historique/', historique_fournisseurs, name='historique_fournisseurs'),
    path('demande_fournisseur/<int:pk>/edit/', edit_demande, name='edit_demande'),
    path('demande_fournisseur/<int:pk>/delete/', delete_demande, name='delete_demande'),
    path('date_range/', date_range, name='date_range'),
    
    # API ENDPOINTS
    path('api/suppliers-by-category/', api_suppliers_by_category, name='api_suppliers_by_category'),
    path('api/products-by-category/', api_products_by_category, name='api_products_by_category'),
    path('api/update-demande-state/', api_update_demande_state, name='api_update_demande_state'),
]
