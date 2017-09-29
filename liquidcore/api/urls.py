from django.conf.urls import url, include
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from .views import *

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'nodes', NodeViewSet)

urlpatterns = format_suffix_patterns([
    url(r'^network/status/$', network_status),
    url(r'^network/domain/$', NetworkDomain.as_view()),
    url(r'^network/lan/$', NetworkLan.as_view()),
    url(r'^network/wan/$', NetworkWan.as_view()),
    url(r'^network/ssh/$', NetworkSsh.as_view()),
]) + [
    url(r'^', include(router.urls)),
]
