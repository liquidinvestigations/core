import qrcode
import tempfile
from base64 import b32encode
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.conf import settings


def create(user):
    return TOTPDevice.objects.create(
        user=user,
        name=user.get_username(),
        confirmed=False,
    )


def add(user):
    return TOTPDevice.objects.create(
        user=user,
        name=user.get_username() +
        str(sum(1 for device in TOTPDevice.objects.devices_for_user(user))),
        confirmed=True,
    )


def get(user, id):
    return TOTPDevice.objects.devices_for_user(user).get(id=id)


def delete_all(user, keep=None):
    for old_device in TOTPDevice.objects.devices_for_user(user):
        if old_device == keep:
            continue
        old_device.delete()


def qrencode(data):
    qr = qrcode.make(data)
    qr_tempfile = tempfile.NamedTemporaryFile()
    qr.save(qr_tempfile.name, 'PNG')
    qr_img = qr_tempfile.read()
    qr_tempfile.close()
    return qr_img


def qr_png(device, username):
    tpl = 'otpauth://totp/{app}:{username}?secret={secret}&issuer={app}'
    url = tpl.format(
        app=settings.LIQUID_2FA_APP_NAME,
        username=username,
        secret=b32encode(device.bin_key).decode('utf8'),
    )
    return qrencode(url)
