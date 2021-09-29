import logging
import string

import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_out
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .auth import kill_sessions

log = logging.getLogger(__name__)
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
def create_user_everywhere(sender, instance, created=None, **kwargs):
    if created:
        payload = {
            "Meta": {
                "USERNAME": instance.username
            }
        }
        res = requests.post('http://10.66.60.1:4646/v1/job/liquid-createuser/dispatch', json=payload)
        if res.status_code != 200:
            log.warning('Error creating user ' + '"' + instance.username + '".')
            log.warning('Nomad returned: ' + str(res.status_code) + ', ' + res.text)
        else:
            log.warning('Created liquid user ' + '"' + instance.username + '".')
