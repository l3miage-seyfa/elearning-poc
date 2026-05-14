from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # CRUD Personnes
    path('personnes/', views.person_list, name='person_list'),
    path('personnes/creer/', views.person_create, name='person_create'),
    path('personnes/<int:pk>/modifier/', views.person_edit, name='person_edit'),
    path('personnes/<int:pk>/supprimer/', views.person_delete, name='person_delete'),
]
