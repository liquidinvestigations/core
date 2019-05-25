from django.urls import path, include
from ..home import views


def _urlpatterns():
    yield path('accounts/', include('django.contrib.auth.urls'))
    yield path('accounts/profile', views.profile)
    yield path('o/', include('oauth2_provider.urls', namespace='oauth2_provider'))
    yield path('', views.homepage)


urlpatterns = list(_urlpatterns())
