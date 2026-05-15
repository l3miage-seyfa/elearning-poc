from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # ── Tableau de bord ────────────────────────────────────────────────────────
    path('tableau-de-bord/', views.admin_dashboard, name='admin_dashboard'),
    path('mes-cours/', views.member_courses, name='member_courses'),

    # ── Cours (review / actions) ───────────────────────────────────────────────
    path('cours/<int:pk>/slides/', views.review_slides, name='review_slides'),
    path('cours/<int:pk>/questions/', views.review_questions, name='review_questions'),
    path('cours/<int:pk>/questions/apercu/', views.preview_questions, name='preview_questions'),
    path('cours/<int:pk>/publier/', views.course_publish, name='course_publish'),
    path('cours/<int:pk>/supprimer/', views.course_delete, name='course_delete'),

    # ── Groupe responsable ─────────────────────────────────────────────────────
    path('groupe/<int:pk>/', views.responsible_group_detail, name='responsible_group'),
    path('groupe/<int:pk>/membres/ajouter/', views.group_add_member, name='group_add_member'),
    path('groupe/<int:pk>/membres/<int:person_pk>/retirer/', views.group_remove_member, name='group_remove_member'),
    path('groupe/<int:pk>/fichiers/upload/', views.group_file_upload, name='group_file_upload'),
    path('groupe/<int:pk>/fichiers/<int:file_pk>/renommer/', views.group_file_rename, name='group_file_rename'),
    path('groupe/<int:pk>/fichiers/<int:file_pk>/supprimer/', views.group_file_delete, name='group_file_delete'),
    path('groupe/<int:pk>/fichiers/<int:file_pk>/telecharger/', views.group_file_download, name='group_file_download'),
    path('groupe/<int:pk>/fichiers/<int:file_pk>/voir/', views.group_file_view, name='group_file_view'),
    path('groupe/<int:pk>/creer-cours/', views.course_create_wizard, name='course_create_wizard'),

    # ── Utilitaires ────────────────────────────────────────────────────────────
    path('membres/autocomplete/', views.member_autocomplete, name='member_autocomplete'),
]
