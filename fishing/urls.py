from django.urls import path
from . import views

app_name = 'fishing'

urlpatterns = [
    path('', views.home, name='home'),
    path('health/', views.health_check, name='health_check'),
    path('lookup/', views.player_lookup, name='player_lookup'),
    path('profile/<str:uuid>/<str:profile_id>/', views.profile_detail, name='profile_detail'),
]
