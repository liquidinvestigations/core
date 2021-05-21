from base64 import b64encode
from django.db import transaction
from django.shortcuts import render
from . import devices
from . import invitations


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
