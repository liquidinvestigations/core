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

if settings.LIQUID_2FA:
    from ..twofactor import views as twofactor_views
    from django.contrib.auth.views import LoginView

    urlpatterns += [
        path('invitation/<code>', twofactor_views.invitation),
        path('accounts/login/', LoginView.as_view()),
    ]
