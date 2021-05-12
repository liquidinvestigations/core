from django.conf import settings
from django.urls import path, include
from .admin import liquid_admin
from ..home import views

urlpatterns = [
    path('admin/', liquid_admin.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profile', views.profile),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('', views.homepage),
]

if settings.LIQUID_2FA:
    from django.contrib.auth.views import LoginView
    from django_otp.forms import OTPAuthenticationForm
    from ..twofactor import views as twofactor_views

    login_view = LoginView.as_view(authentication_form=OTPAuthenticationForm)

    urlpatterns = [
        path('accounts/login/', login_view),
        path('invitation/<code>', twofactor_views.invitation),
        path('accounts/change_totp/', twofactor_views.change_totp),
        path('accounts/change_totp/confirm',
             twofactor_views.confirm_totp_change),
    ] + urlpatterns
