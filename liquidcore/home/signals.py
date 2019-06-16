import json
import base64
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_out
from django.contrib.sessions.models import Session


@receiver(user_logged_out)
def kill_sessions(user, **kwargs):
    # delete oauth2 access and refresh tokens for the user
    user.oauth2_provider_accesstoken.all().delete()
    user.oauth2_provider_refreshtoken.all().delete()

    # delete all Django sessions for the user
    for session in Session.objects.all().iterator():
        session_json = base64.b64decode(session.session_data).split(b':', 1)[1]
        user_id = json.loads(session_json).get('_auth_user_id')
        if user_id and int(user_id) == user.id:
            session.delete()
