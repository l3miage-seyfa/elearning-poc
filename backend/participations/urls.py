from django.urls import path
from . import views

app_name = 'participations'

urlpatterns = [
    path('quiz/<int:course_pk>/', views.take_quiz, name='take_quiz'),
    path('resultat/<int:pk>/', views.result, name='result'),
    path('resultat/<int:pk>/detail/', views.result_detail, name='result_detail'),
    path('historique/', views.my_history, name='my_history'),
    path('slides/<int:course_pk>/', views.slide_reader, name='slide_reader'),
    path('slides/<int:course_pk>/question/', views.ask_question, name='ask_question'),
]
