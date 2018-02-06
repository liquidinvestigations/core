import os
import json
import subprocess
import shlex
from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_out
from django.conf import settings


def invoke_hook(name, *args, env={}):
    quoted_args = ' '.join(shlex.quote(a) for a in [name] + list(args))
    command = settings.INVOKE_HOOK + " " + quoted_args
    print('invoke hook', command)

    try:
        subprocess.run(
            command,
            env=dict(os.environ, **env),
            check=True,
            shell=True,
        )
    except Exception as e:
        print('something failed :(', e)
        raise


def random_password():
    import random
    urandom = random.SystemRandom()
    vocabulary = ('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                  '0123456789!@#$%^&*()-=+[]{}:.<>/?')
    return ''.join(urandom.choice(vocabulary) for _ in range(16))


def on_user_save(sender, instance, created, **kwargs):
    if created:
        username = instance.get_username()
        password = instance._password
        if not password:
            password = random_password()
        invoke_hook('user-created', username, env={
            'LIQUID_HOOK_DATA': json.dumps({
                'password': password,
            }),
        })

    else:
        password = instance._password
        if password is not None:
            username = instance.get_username()
            invoke_hook('user-passwd', username, env={
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


def on_logout(sender, **kwargs):
    user = kwargs['user']
    user.accesstoken_set.all().delete()
    user.refreshtoken_set.all().delete()


user_logged_out.connect(on_logout)
