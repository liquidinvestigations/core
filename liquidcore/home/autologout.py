from datetime import timedelta
from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.utils import timezone


def AutoLogoutMiddleware(get_response):
    if not settings.AUTH_AUTO_LOGOUT:
        return get_response

    def middleware(request):
        user = request.user
        if user.is_authenticated:
            login_time = user.last_login
            logout_time = login_time + \
                settings.AUTH_AUTO_LOGOUT + timedelta(minutes=59)
            now = timezone.now()
            if now > logout_time:
                logout(request)
                login = "{}?next={}".format(settings.LOGIN_URL, request.path)
                return HttpResponseRedirect(login)

        return get_response(request)

    return middleware
