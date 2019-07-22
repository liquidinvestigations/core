import json
import base64
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.sessions.models import Session
from oauth2_provider.models import RefreshToken, AccessToken

staff_only = settings.AUTH_STAFF_ONLY


class AuthBackend(ModelBackend):

    def user_can_authenticate(self, user):
        if staff_only and not user.is_staff:
            return False

        return super().user_can_authenticate(user)


def kill_sessions(user=None):
    """
    Delete oauth2 access and refresh tokens, for `user` if specified, or for
    everybody if `user == None`.
    """

    if user:
        # for the user
        access_tokens = user.oauth2_provider_accesstoken.all()
        refresh_tokens = user.oauth2_provider_refreshtoken.all()
    else:
        # for everybody
        access_tokens = AccessToken.objects.all()
        refresh_tokens = RefreshToken.objects.all()

    access_tokens.delete()
    refresh_tokens.delete()

    # delete all Django sessions
    if user:
        # for the user
        for session in Session.objects.all().iterator():
            session_data = base64.b64decode(session.session_data)
            session_json = session_data.split(b':', 1)[1]
            user_id = json.loads(session_json).get('_auth_user_id')
            if user_id and int(user_id) == user.id:
                session.delete()
    else:
        # for everybody
        Session.objects.all().delete()
