import subprocess
from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.models import User
from django.conf import settings

if settings.HYPOTHESIS_USER_SCRIPTS:

    def create_hypothesis_user(sender, instance, created, **kwargs):
        if created:
            script = settings.HYPOTHESIS_USER_SCRIPTS['create']
            username = instance.get_username()
            password = instance._password
            subprocess.check_call([script, username, password])

        else:
            password = instance._password
            if password is not None:
                script = settings.HYPOTHESIS_USER_SCRIPTS['passwd']
                username = instance.get_username()
                subprocess.check_call([script, username, password])

    post_save.connect(
        create_hypothesis_user,
        sender=User,
        dispatch_uid='create_hypothesis_user',
    )

    def delete_hypothesis_user(sender, instance, **kwargs):
        script = settings.HYPOTHESIS_USER_SCRIPTS['delete']
        username = instance.get_username()
        subprocess.check_call([script, username])

    pre_delete.connect(
        delete_hypothesis_user,
        sender=User,
        dispatch_uid='delete_hypothesis_user',
    )
