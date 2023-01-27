from django.db import transaction
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate, login, get_user_model
from django.utils.timezone import now
from django.shortcuts import render
from django_otp import login as otp_login
from . import models
from . import devices


@transaction.atomic
def invite(username, duration, operator=None, create=False):
    if create:
        user = get_user_model().objects.create(username=username)
    else:
        user = get_user_model().objects.get_by_natural_key(username)

    models.Invitation.objects.filter(user=user).delete()
    invitation = models.Invitation.objects.create(
        user=user,
        expires=now() + timedelta(minutes=duration),
    )

    return f'{settings.LIQUID_URL}/invitation/{invitation.code}'


def get(code):
    '''Checks if an invitation is expired and returns the invitation.'''
    invitation = (
        models.Invitation.objects
        .select_for_update()
        .filter(code=code)
    ).first()

    if invitation is None:
        return None

    return invitation


def device_for_session(request, invitation):
    '''Creates a fresh device for a user for each invitation.

    Also removes all old devices first so that multiple invitations
    don't lead to multiple devices for that user.
    If the invitation is already associated to a device returns that
    device.
    '''
    if invitation.device:
        return invitation.device
    user = invitation.user
    devices.delete_all(user)
    device = devices.create(user)
    invitation.device = device
    invitation.save()
    return device


@transaction.atomic
def accept(request, invitation, device, password):
    user = invitation.user
    user.set_password(password)
    user.save()
    device.confirmed = True
    device.save()
    devices.delete_all(user, keep=device)
    invitation.used = True
    invitation.save()
    user2 = authenticate(username=user.get_username(), password=password)
    assert user2
    login(request, user2)
    otp_login(request, device)


def create_invitations(modeladmin, request, queryset):
    username_list = [u.username for u in queryset]
    duration = settings.LIQUID_2FA_INVITATION_VALID
    invitations = [
        (username, invite(username, duration, request.user))
        for username in username_list
    ]
    return render(request, 'admin-create-invitations.html', {
        'invitations': invitations,
    })


create_invitations.short_description = "Create invitations"
