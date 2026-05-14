from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('mes-cours/', views.member_courses, name='member_courses'),
    path('creer/', views.course_create, name='course_create'),
    path('upload-pdf/', views.upload_pdf_view, name='upload_pdf'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
]
