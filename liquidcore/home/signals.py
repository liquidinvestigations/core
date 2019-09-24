import string
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_out
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .auth import kill_sessions


USERNAME_CHARS = string.ascii_letters + string.digits + '.'
User = get_user_model()


@receiver(user_logged_out)
def kill_user_sessions(user, **kwargs):
    kill_sessions(user=user)


@receiver(pre_save, sender=User)
def check_user_username(sender, instance, **kwargs):
    assert all(x in USERNAME_CHARS for x in instance.username), \
        f'Bad username: "{instance.username}"'
