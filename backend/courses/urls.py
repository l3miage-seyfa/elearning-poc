from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('mes-cours/', views.member_courses, name='member_courses'),
    path('<int:pk>/review/slides/', views.review_slides, name='review_slides'),
    path('<int:pk>/review/questions/', views.review_questions, name='review_questions'),
    path('<int:pk>/publier/', views.course_publish, name='course_publish'),
    path('<int:pk>/supprimer/', views.course_delete, name='course_delete'),
    path('groupe/<int:pk>/responsable/', views.responsible_group_detail, name='responsible_group'),
    path('groupe/<int:pk>/ajouter-membre/', views.group_add_member, name='group_add_member'),
    path('groupe/<int:pk>/retirer-membre/<int:person_pk>/', views.group_remove_member, name='group_remove_member'),
    path('groupe/<int:pk>/fichiers/upload/', views.group_file_upload, name='group_file_upload'),
    path('groupe/<int:pk>/fichiers/<int:file_pk>/renommer/', views.group_file_rename, name='group_file_rename'),
    path('groupe/<int:pk>/fichiers/<int:file_pk>/supprimer/', views.group_file_delete, name='group_file_delete'),
    path('groupe/<int:pk>/fichiers/<int:file_pk>/telecharger/', views.group_file_download, name='group_file_download'),
    path('groupe/<int:pk>/cours/creer/', views.course_create_wizard, name='course_create_wizard'),
    path('membres/autocomplete/', views.member_autocomplete, name='member_autocomplete'),
]
