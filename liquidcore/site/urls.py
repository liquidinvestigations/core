from django.contrib import admin
from django.urls import path, include
from ..home import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profile', views.profile),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('', views.homepage),
]
