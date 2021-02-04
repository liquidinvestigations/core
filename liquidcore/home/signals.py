import string
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_out
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .auth import kill_sessions
from .models import Profile


USERNAME_CHARS = string.ascii_letters + string.digits + '.'
User = get_user_model()


@receiver(user_logged_out)
def kill_user_sessions(user, **kwargs):
    kill_sessions(user=user)


@receiver(pre_save, sender=User)
def check_user_username(sender, instance, **kwargs):
    assert all(x in USERNAME_CHARS for x in instance.username), \
        f'Bad username: "{instance.username}"'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        return
    try:
        instance.profile.save()
    except User.profile.RelatedObjectDoesNotExist:
        Profile.objects.create(user=instance)
        return
