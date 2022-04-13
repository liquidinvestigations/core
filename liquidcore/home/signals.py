import logging
import string

import requests
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
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
        nomad_url = os.getenv('NOMAD_URL')
        if nomad_url:
            res = requests.post(
                f'{nomad_url}/v1/job/liquid-createuser/dispatch',
                json=payload
            )
            if res.status_code != 200:
                log.warning(f'Error creating user "{instance.username}".')
                log.warning(
                    f'Nomad returned: {str(res.status_code)}, {res.text}'
                )
            else:
                log.warning(f'Created liquid user "{instance.username}".')
        else:
            log.warning('No nomad address found to create liquid users!')


@receiver(post_save, sender=User)
def add_default_permissions(sender, instance, created, **kwargs):
    '''Signal handler to add default permissions
    after user has been created.'''
    if created:
        rocketchat_perm = Permission.objects.get(codename='use_rocketchat')
        hypothesis_perm = Permission.objects.get(codename='use_hypothesis')
        instance.user_permissions.add(rocketchat_perm)
        instance.user_permissions.add(hypothesis_perm)
        instance.save()
