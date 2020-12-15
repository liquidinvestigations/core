from django.conf import settings
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

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
    ] + urlpatterns

# DRF-YASG
# ========
if settings.DEBUG:
    schema_view = get_schema_view(
        openapi.Info(
            title="Core API",
            default_version='v0',
            # description="Liquid API for Tags",
            # contact=openapi.Contact(email="contact@liquiddemo.org"),
            # license=openapi.License(name="MIT License"),
        ),
        public=True,
        permission_classes=[permissions.AllowAny],
        validators=['ssv'],
    )

    schema_urlpatterns = [
        re_path(r'^swagger(?P<format>\.json|\.yaml)$',
                schema_view.without_ui(cache_timeout=0), name='schema-json'),
        re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]

    urlpatterns += schema_urlpatterns
