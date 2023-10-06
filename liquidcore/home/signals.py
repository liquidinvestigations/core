import logging
import string

import requests
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.signals import user_logged_out
from django.db.models import signals
from django.dispatch import receiver

from .auth import kill_sessions
from . import sessions

log = logging.getLogger(__name__)
USERNAME_CHARS = string.ascii_letters + string.digits + '.'
# USERNAME_REGEX = r'[' + USERNAME_CHARS + r']{1,150}'
User = get_user_model()


@receiver(user_logged_out)
def kill_user_sessions(user, **kwargs):
    kill_sessions(user=user)


@receiver(signals.pre_save, sender=User)
def check_user_username(sender, instance, **kwargs):
    assert all(x in USERNAME_CHARS for x in instance.username), \
        f'Bad username: "{instance.username}"'


@receiver(signals.post_save, sender=User)
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


@receiver(signals.post_delete, sender=User)
def delete_user_everywhere(sender, instance, **kwargs):
    payload = {
        "Meta": {
            "USERNAME": instance.username
        }
    }
    nomad_url = os.getenv('NOMAD_URL')
    if nomad_url:
        res = requests.post(
            f'{nomad_url}/v1/job/liquid-deleteuser/dispatch',
            json=payload
        )
        if res.status_code != 200:
            log.warning(f'Error deleting user "{instance.username}".')
            log.warning(
                f'Nomad returned: {str(res.status_code)}, {res.text}'
            )
        else:
            log.warning(f'Deleted liquid user "{instance.username}".')
    else:
        log.warning('No nomad address found to delete liquid users!')


@receiver(signals.post_save, sender=User)
def add_default_permissions(sender, instance, created, **kwargs):
    '''Signal handler to add default permissions
    after user has been created.'''
    if created:
        rocketchat_perm = Permission.objects.get(codename='use_rocketchat')
        hypothesis_perm = Permission.objects.get(codename='use_hypothesis')
        instance.user_permissions.add(rocketchat_perm)
        instance.user_permissions.add(hypothesis_perm)
        instance.save()


@receiver(user_logged_out)
def delete_authproxy_sessions_logout(user, **kwargs):
    sessions.clear_authproxy_session(user.username)
    log.warning((f'Removed app sessions for user: "{user.username}" '
                 'after logout.'))


@receiver(signals.pre_save, sender=User)
def delete_authproxy_sessions_inactive(sender, instance, **kwargs):
    if instance.id is None:
        return
    else:
        try:
            previous = sender.objects.get(id=instance.id)
        except User.DoesNotExist:
            return
        if previous.is_active and not instance.is_active:
            sessions.clear_authproxy_session(instance.username)
            log.warning((f'User "{instance.username}" disabled. '
                         'Removed all app sessions.'))


@receiver(signals.pre_delete, sender=User)
def delete_authproxy_sessions_delete(sender, instance, **kwargs):
    sessions.clear_authproxy_session(instance.username)
    log.warning((f'User "{instance.username}" deleted. '
                 'Removed all app sessions.'))


@receiver(signals.m2m_changed, sender=User.user_permissions.through)
def delete_authproxy_sessions_permissions(sender, instance, action, **kwargs):
    if action == 'pre_remove':
        sessions.clear_authproxy_session(instance.username)
        log.warning((f'App permission removed from "{instance.username}". '
                     'Removed all app sessions.'))
