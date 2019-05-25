from django.conf.urls import include, url
from . import views


def _urlpatterns():
    yield url(r'^accounts/', include('django.contrib.auth.urls'))
    yield url(r'^accounts/profile$', views.profile)
    yield url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider'))
    yield url(r'^', include('liquidcore.home.urls'))


urlpatterns = list(_urlpatterns())
