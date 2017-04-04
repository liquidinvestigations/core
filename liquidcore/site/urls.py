from django.conf.urls import include, url
from django.contrib import admin
from ..home import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^accounts/profile$', views.profile),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^', include('liquidcore.home.urls')),
]
