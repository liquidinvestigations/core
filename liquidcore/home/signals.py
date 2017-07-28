import os
import json
import subprocess
from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.models import User
from django.conf import settings


def invoke_hook(name, *args, env={}):
    subprocess.run(
        [settings.INVOKE_HOOK, name] + list(args),
        env=dict(os.environ, **env),
        check=True,
    )


def on_user_save(sender, instance, created, **kwargs):
    if created:
        username = instance.get_username()
        password = instance._password
        invoke_hook('user-created', username, env={
            'LIQUID_HOOK_DATA': json.dumps({
                'password': password,
            }),
        })

    else:
        password = instance._password
        if password is not None:
            username = instance.get_username()
            invoke_hook('user-created', username, env={
                'LIQUID_HOOK_DATA': json.dumps({
                    'password': password,
                }),
            })

post_save.connect(
    on_user_save,
    sender=User,
    dispatch_uid='on_user_save',
)


def on_user_delete(sender, instance, **kwargs):
    username = instance.get_username()
    invoke_hook('user-deleted', username)

pre_delete.connect(
    on_user_delete,
    sender=User,
    dispatch_uid='on_user_delete',
)
