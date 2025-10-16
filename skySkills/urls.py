from django.contrib import admin
from django.urls import path, include
from fishing.views import health_check, home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('', home, name='home'),
    path('fishing/', include('fishing.urls')),
]
