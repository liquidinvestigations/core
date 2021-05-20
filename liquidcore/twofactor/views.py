from base64 import b64encode
from django.db import transaction
from django.shortcuts import render, redirect
from . import devices
from . import invitations
import django_otp
from django.contrib.auth import authenticate


@transaction.atomic
def invitation(request, code):
    invitation = invitations.get_or_404(code)
    bad_token = None
    bad_username = False
    bad_password = False
    username = invitation.user.get_username()

    device = invitations.device_for_session(request, invitation)

    if request.method == 'POST':
        if not device.verify_token(request.POST['code']):
            bad_token = True

        if request.POST['username'] != username:
            bad_username = True

        password = request.POST['password']
        if password != request.POST['password-confirm']:
            bad_password = True

        if not (bad_username or bad_password or bad_token):
            invitations.accept(request, invitation, device, password)
            return render(request, 'totp-invitation-success.html')

    png_data = b64encode(devices.qr_png(device, username)).decode('utf8')
    otp_png = 'data:image/png;base64,' + png_data

    return render(request, 'totp-invitation-form.html', {
        'username': username,
        'otp_png': otp_png,
        'bad_username': bad_username,
        'bad_password': bad_password,
        'bad_token': bad_token,
    })


@transaction.atomic
def change_totp(request, add=False):
    bad_token = None
    bad_password = False
    bad_device_name = False
    user = request.user

    if add:
        request.session['add_device'] = True
    else:
        request.session['add_device'] = False

    if request.method == 'POST' and 'token' in request.POST:
        device = django_otp.match_token(user, request.POST['token'])
        if not device:
            bad_token = True
        password = request.POST['password']

        if not authenticate(username=user.username, password=password):
            bad_password = True

        if not request.POST['new_name']:
            bad_device_name = True
        else:
            new_name = request.POST['new_name']

        if not (bad_password or bad_token or bad_device_name):
            new_device = devices.create(user, new_name)
            new_device.confirmed = True
            new_device.save()
            request.session['new_device'] = new_device.id

            png_data = b64encode(devices.qr_png(new_device,
                                                user.username)).decode('utf8')

            otp_png = 'data:image/png;base64,' + png_data

            request.session['otp_png'] = otp_png

            return redirect(confirm_totp_change)

    return render(request, 'totp-change-form.html', {
        'bad_token': bad_token,
        'bad_password': bad_password,
        'bad_device_name': bad_device_name,
        'add_device': request.session['add_device'],
    })


@transaction.atomic
def confirm_totp_change(request):
    bad_token = None
    user = request.user
    new_device = devices.get(user, request.session['new_device'])
    otp_png = request.session['otp_png']
    add_device = request.session['add_device']
    success = False

    if request.method == 'POST':
        new_token = request.POST['new_token']
        if new_device.verify_token(new_token):
            success = True
            if not add_device:
                devices.delete_all(user, keep=new_device)
        else:
            bad_token = True

    return render(request, 'totp-change-confirmation.html', {
        'success': success,
        'bad_token': bad_token,
        'otp_png': otp_png,
    })


def totp_settings(request):
    return render(request, 'totp-settings.html', {
        'devices': django_otp.devices_for_user(request.user),
    })


def totp_add(request):
    return change_totp(request, True)


@transaction.atomic
def totp_remove(request):
    bad_token = False
    bad_password = False
    user = request.user
    success = False

    if request.method == 'POST' and 'token' in request.POST:
        device = django_otp.match_token(user, request.POST['token'])
        if not device:
            bad_token = True
        password = request.POST['password']

        if not authenticate(username=user.username, password=password):
            bad_password = True

        if not bad_password and not bad_token:
            keep_device = devices.get(user, request.POST['device'])
            devices.delete_all(user, keep_device)
            success = True

    return render(request, 'totp-remove.html', {
        'devices': django_otp.devices_for_user(request.user),
        'bad_token': bad_token,
        'bad_password': bad_password,
        'success': success,
    })
