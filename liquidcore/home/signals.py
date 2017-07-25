import subprocess
from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.models import User
from django.conf import settings

if settings.INVOKE_HOOK:

    def invoke_hook(name, *args, env={}):
        subprocess.run([settings.INVOKE_HOOK] + args, check=True)

    def create_hypothesis_user(sender, instance, created, **kwargs):
        if created:
            username = instance.get_username()
            password = instance._password
            invoke_hook('user-created', username, env={
                'PASSWORD': password,
            })

        else:
            password = instance._password
            if password is not None:
                username = instance.get_username()
                invoke_hook('user-created', username, env={
                    'PASSWORD': password,
                })

    post_save.connect(
        create_hypothesis_user,
        sender=User,
        dispatch_uid='create_hypothesis_user',
    )

    def delete_hypothesis_user(sender, instance, **kwargs):
        username = instance.get_username()
        invoke_hook('user-deleted', username)

    pre_delete.connect(
        delete_hypothesis_user,
        sender=User,
        dispatch_uid='delete_hypothesis_user',
    )
