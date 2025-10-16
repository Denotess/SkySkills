from django.urls import path
from . import views

app_name = 'skills'

urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.skill_list, name='skill_list'),
]