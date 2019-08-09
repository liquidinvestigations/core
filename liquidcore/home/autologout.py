from time import time
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.http import HttpResponseRedirect

login_time_session_key = 'hoover.contrib.twofactor.login_time'


@receiver(user_logged_in)
def on_login_success(sender, request, **kwargs):
    request.session[login_time_session_key] = time()


def AutoLogoutMiddleware(get_response):
    auto_logout = settings.AUTH_AUTO_LOGOUT
    if not auto_logout:
        return get_response

    assert auto_logout.endswith('h')
    interval = int(auto_logout[:-1]) * 3600

    def middleware(request):
        user = request.user
        if user.is_authenticated:
            login_time = request.session.get(login_time_session_key) or 0
            logout_time = login_time + interval
            if time() > logout_time:
                logout(request)
                login = "{}?next={}".format(settings.LOGIN_URL, request.path)
                return HttpResponseRedirect(login)

        return get_response(request)

    return middleware
