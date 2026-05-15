from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('tableau-de-bord/', views.dashboard, name='dashboard'),
    # CRUD Membres (admin uniquement)
    path('membres/', views.person_list, name='person_list'),
    path('membres/creer/', views.person_create, name='person_create'),
    path('membres/<int:pk>/modifier/', views.person_edit, name='person_edit'),
    path('membres/<int:pk>/supprimer/', views.person_delete, name='person_delete'),
]
