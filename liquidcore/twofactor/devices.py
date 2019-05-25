import subprocess
from base64 import b32encode
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.conf import settings


def create(user):
    return TOTPDevice.objects.create(
        user=user,
        name=user.get_username(),
        confirmed=False,
    )

def get(user, id):
    return TOTPDevice.objects.devices_for_user(user).get(id=id)

def delete_all(user, keep=None):
    for old_device in TOTPDevice.objects.devices_for_user(user):
        if old_device == keep:
            continue
        old_device.delete()

def qrencode(data):
    return subprocess.check_output(['qrencode', data, '-s', '5', '-o', '-'])

def qr_png(device, username):
    tpl = 'otpauth://totp/{app}:{username}?secret={secret}&issuer={app}'
    url = tpl.format(
        app=settings.LIQUID_2FA_APP_NAME,
        username=username,
        secret=b32encode(device.bin_key).decode('utf8'),
    )
    return qrencode(url)
