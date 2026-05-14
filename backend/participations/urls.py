from django.urls import path
from . import views

app_name = 'participations'

urlpatterns = [
    path('quiz/<int:course_pk>/', views.take_quiz, name='take_quiz'),
    path('resultat/<int:pk>/', views.result, name='result'),
]
