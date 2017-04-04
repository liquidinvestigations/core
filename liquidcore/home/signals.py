import subprocess
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.conf import settings

if settings.HYPOTHESIS_CREATE_USER_SCRIPT:

    def create_hypothesis_user(sender, instance, created, **kwargs):
        if created:
            script = settings.HYPOTHESIS_CREATE_USER_SCRIPT
            username = instance.get_username()
            password = instance._password
            subprocess.check_call([script, username, password])

    post_save.connect(
        create_hypothesis_user,
        sender=User,
        dispatch_uid='create_hypothesis_user',
    )
