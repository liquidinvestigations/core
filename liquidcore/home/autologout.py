from datetime import timedelta
from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.utils import timezone


def get_interval(spec):
    if not spec:
        return None

    if spec.endswith('d'):
        return timedelta(days=int(spec[:-1]))

    if spec.endswith('h'):
        return timedelta(hours=int(spec[:-1]))

    if spec.endswith('m'):
        return timedelta(minutes=int(spec[:-1]))

    if spec.endswith('s'):
        return timedelta(seconds=int(spec[:-1]))

    raise RuntimeError(f"Can't parse interval {spec!r}")


auto_logout = get_interval(settings.AUTH_AUTO_LOGOUT)


def AutoLogoutMiddleware(get_response):
    if not auto_logout:
        return get_response

    def middleware(request):
        user = request.user
        if user.is_authenticated:
            login_time = user.last_login
            logout_time = login_time + auto_logout
            now = timezone.now()
            if now > logout_time:
                logout(request)
                login = "{}?next={}".format(settings.LOGIN_URL, request.path)
                return HttpResponseRedirect(login)

        return get_response(request)

    return middleware
