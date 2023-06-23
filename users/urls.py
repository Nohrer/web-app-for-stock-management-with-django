
from django.urls import path
from .views import magasinier_login, dashboard_magasinier, logout_user, magasinier_registration, employee_registration, directeur_registration, dashboard_directeur, dashboard_employee

app_name = 'users'
urlpatterns = [
    path('', magasinier_login, name='magasinier_login'),
    path('dashboard/magasinier/', dashboard_magasinier,
         name='dashboard_magasinier'),
    path('dashboard/directeur/', dashboard_directeur, name='dashboard_directeur'),
    path('dashboard/employee/', dashboard_employee, name='dashboard_employee'),
    path('logout_user/', logout_user, name='logout_user'),

    path('magasinier_registration/', magasinier_registration,
         name='magasinier_registration'),
    path('employee_registration/', employee_registration,
         name='employee_registration'),
    path('directeur_registration/', directeur_registration,
         name='directeur_registration'),
]
