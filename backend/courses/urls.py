from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('mes-cours/', views.member_courses, name='member_courses'),
    path('creer/', views.course_create, name='course_create'),
    path('upload-pdf/', views.upload_pdf_view, name='upload_pdf'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('<int:pk>/review/slides/', views.review_slides, name='review_slides'),
    path('<int:pk>/review/questions/', views.review_questions, name='review_questions'),
    path('<int:pk>/publier/', views.course_publish, name='course_publish'),
    path('<int:pk>/supprimer/', views.course_delete, name='course_delete'),
    path('groupe/<int:pk>/responsable/', views.responsible_group_detail, name='responsible_group'),
]
