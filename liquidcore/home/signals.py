from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_out
from .auth import kill_sessions


@receiver(user_logged_out)
def kill_user_sessions(user, **kwargs):
    kill_sessions(user=user)
