from base64 import b64encode
from django.db import transaction
from django.shortcuts import render
from . import devices
from . import invitations
import django_otp
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required


def get_png(user, device):
    png_data = b64encode(devices.qr_png(device,
                         user.get_username())).decode('utf8')
    return 'data:image/png;base64,' + png_data


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


def add_device(user, name):
    device = devices.create(user, name)
    device.confirmed = True
    device.save()
    return device


@login_required
@transaction.atomic
def change_totp(request, add=False):
    bad_password = False
    bad_token = None
    success = False
    otp_png = None
    confirmed = False

    request.session['add_device'] = add

    if request.method == 'POST' and 'token' in request.POST:

        if not django_otp.match_token(request.user, request.POST['token']):
            bad_token = True

        if not authenticate(username=request.user.username,
                            password=request.POST['password']):
            bad_password = True

        if not (bad_password or bad_token):
            new_device = add_device(request.user, request.POST['new_name'])
            request.session['new_device'] = new_device.id
            otp_png = get_png(request.user, new_device)

    if request.method == 'POST' and 'new_token' in request.POST:
        new_device = devices.get(request.user, request.session['new_device'])
        otp_png = get_png(request.user, new_device)
        if new_device.verify_token(request.POST['new_token']):
            confirmed = True
            if not request.session['add_device']:
                devices.delete_all(request.user, keep=new_device)
        else:
            bad_token = True

    return render(request, 'totp-change-form.html', {
        'bad_token': bad_token,
        'bad_password': bad_password,
        'add_device': request.session['add_device'],
        'otp_png': otp_png,
        'success': success,
        'confirmed': confirmed,
    })


@login_required
def totp_settings(request):
    return render(request, 'totp-settings.html', {
        'devices': django_otp.devices_for_user(request.user),
    })


@login_required
def totp_add(request):
    return change_totp(request, True)


@login_required
@transaction.atomic
def totp_remove(request):
    bad_token = False
    bad_password = False
    success = False

    if request.method == 'POST' and 'token' in request.POST:
        device = django_otp.match_token(request.user, request.POST['token'])
        if not device:
            bad_token = True

        if not authenticate(username=request.user.username,
                            password=request.POST['password']):
            bad_password = True

        if not bad_password and not bad_token:
            devices.delete_all(request.user, keep=device)
            success = True

    return render(request, 'totp-remove.html', {
        'bad_token': bad_token,
        'bad_password': bad_password,
        'success': success,
    })
