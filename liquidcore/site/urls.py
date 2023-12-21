from django.conf import settings
from django.urls import path, include, re_path
from django.shortcuts import redirect
from .admin import liquid_admin
from ..home import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', liquid_admin.urls),
    path('accounts/password_change/',
         auth_views.PasswordChangeView.as_view(),
         name='password_change'
         ),
    path('accounts/password_change/done/',
         auth_views.PasswordChangeDoneView.as_view(),
         name='password_change_done'
         ),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/profile', views.profile, name='profile'),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('system-health', views.healthchecks_page, name='healthchecks'),
    path('.well-known/openid-configuration/', lambda request: redirect('o/.well-known/openid-configuration/', permanent=True), name='redir_oidc'),
    path('', views.homepage, name='home'),
]

if settings.LIQUID_2FA:
    from django.contrib.auth.views import LoginView
    from django_otp.forms import OTPAuthenticationForm
    from ..twofactor import views as twofactor_views
    from ..home.forms import OtpPasswordChangeForm

    login_view = LoginView.as_view(authentication_form=OTPAuthenticationForm)

    urlpatterns = [
        path('accounts/login/', login_view, name='login'),
        path('accounts/password_change/',
             auth_views.PasswordChangeView
             .as_view(form_class=OtpPasswordChangeForm,
                      template_name='password_change_form_otp.html'),
             name='password_change'),
        path('invitation/<code>', twofactor_views.invitation),
        path('accounts/totp/change/', twofactor_views.change_totp,
             name='totp_change'),
        path('accounts/totp/settings/',
             twofactor_views.totp_settings, name='totp_settings'),
        path('accounts/totp/add/',
             twofactor_views.totp_add, name='totp_add'),
        path('accounts/totp/remove/',
             twofactor_views.totp_remove, name='totp_remove'),
    ] + urlpatterns

if settings.LIQUID_ENABLE_DASHBOARDS:
    urlpatterns = [
        re_path(r'^grafana.*$', views.proxy_dashboards,
                name='proxy-dashboard-grafana'),
        re_path(r'^nomad.*$', views.proxy_dashboards,
                name='proxy-dashboard-nomad'),
        re_path(r'^_snoop_rabbit.*$', views.proxy_dashboards,
                name='proxy-dashboard-snoop-rabbitmq'),
        re_path(r'^_snoop_pgwatch2.*$', views.proxy_dashboards,
                name='proxy-dashboard-snoop-pgwatch2'),
        re_path(r'^_search_rabbit.*$', views.proxy_dashboards,
                name='proxy-dashboard-search-rabbitmq'),
        re_path(r'^snoop.*$', views.proxy_dashboards,
                name='proxy-dashboard-snoop'),

        re_path(r'^ui/.*$', views.proxy_dashboards,
                name='proxy-dashboard-nomad-ui'),
        re_path(r'^v1.*$', views.proxy_dashboards,
                name='proxy-dashboard-nomad-v1'),
        re_path(r'^consul_ui.*$', views.proxy_dashboards,
                name='proxy-dashboard-consul-ui'),
    ] + urlpatterns
