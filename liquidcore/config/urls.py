from django.conf.urls import url, include
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'services', views.ServiceViewSet)
router.register(r'vpn/server/keys', views.VPNClientKeyViewSet)

urlpatterns = format_suffix_patterns([
    url(r'^network/status/$', views.network_status),
    url(r'^registration/$', views.Registration.as_view()),
    url(r'^network/domain/$', views.NetworkDomain.as_view()),
    url(r'^network/lan/$', views.NetworkLan.as_view()),
    url(r'^network/wan/$', views.NetworkWan.as_view()),
    url(r'^network/ssh/$', views.NetworkSsh.as_view()),
    url(r'^vpn/$', views.vpn_status),
    url(r'^vpn/client/$', views.vpn_client_enabled),
    url(r'^vpn/client/upload/$', views.vpn_client_upload),
    url(r'^vpn/server/$', views.vpn_server_enabled),
    url(r'^nodes/$', views.node_list),
    url(r'^configure/status/$', views.configure_status),
    url(r'^configure/repair/$', views.configure_repair),
    url(r'^shutdown/$', views.api_shutdown),
    url(r'^status/$', views.general_status),
]) + [
    url(r'^', include(router.urls)),
]
