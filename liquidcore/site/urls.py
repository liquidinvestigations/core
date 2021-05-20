from django.conf import settings
from django.urls import path, include
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
    path('accounts/profile', views.profile),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('', views.homepage),
]

if settings.LIQUID_2FA:
    from django.contrib.auth.views import LoginView
    from django_otp.forms import OTPAuthenticationForm
    from ..twofactor import views as twofactor_views
    from ..home.forms import OtpPasswordChangeForm

    login_view = LoginView.as_view(authentication_form=OTPAuthenticationForm)

    urlpatterns = [
        path('accounts/login/', login_view),
        path('accounts/password_change/',
             auth_views.PasswordChangeView
             .as_view(form_class=OtpPasswordChangeForm,
                      template_name='password_change_form_otp.html'),
             name='password_change'),
        path('invitation/<code>', twofactor_views.invitation),
        path('accounts/totp/change/', twofactor_views.change_totp),
        path('accounts/totp/confirm',
             twofactor_views.confirm_totp_change),
        path('accounts/totp/settings/',
             twofactor_views.totp_settings),
        path('accounts/totp/add/',
             twofactor_views.totp_add),
        path('accounts/totp/remove/',
             twofactor_views.totp_remove),
    ] + urlpatterns
