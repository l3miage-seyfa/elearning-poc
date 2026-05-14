from django.urls import path
from . import views

app_name = 'groups'

urlpatterns = [
    path('', views.my_groups, name='my_groups'),
    path('<int:pk>/', views.group_detail, name='group_detail'),
]
