from django.conf import settings
from django.contrib.auth import logout
from django.utils import timezone

from .auth import kill_sessions


def AutoLogoutMiddleware(get_response):
    def middleware(request):
        user = request.user
        if user.is_authenticated:
            login_time = user.last_login
            logout_time = login_time + \
                settings.AUTH_AUTO_LOGOUT
            now = timezone.now()
            if now > logout_time:
                logout(request)
                kill_sessions(user)
                request.session.clear()

        return get_response(request)

    return middleware
