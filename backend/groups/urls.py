from django.urls import path
from . import views

app_name = 'groups'

urlpatterns = [
    path('', views.my_groups, name='my_groups'),
    path('<int:pk>/', views.group_detail, name='group_detail'),
    # CRUD admin
    path('gestion/', views.group_list, name='group_list'),
    path('gestion/creer/', views.group_create, name='group_create'),
    path('gestion/<int:pk>/modifier/', views.group_edit, name='group_edit'),
    path('gestion/<int:pk>/supprimer/', views.group_delete, name='group_delete'),
]
