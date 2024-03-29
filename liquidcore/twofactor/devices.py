import qrcode
import tempfile
from base64 import b32encode
# from django_otp.plugins.otp_totp.models import TOTPDevice
from .models import TOTPDeviceTimed
from django.conf import settings


def create(user, name=None):
    if not name:
        name = user.get_username()

    return TOTPDeviceTimed.objects.create(
        user=user,
        name=name,
        confirmed=False,
    )


def get(user, id):
    return TOTPDeviceTimed.objects.devices_for_user(user).get(id=id)
    # return TOTPDeviceTimed.objects.get(id=id)


def delete_all(user, keep=None):
    for old_device in TOTPDeviceTimed.objects.devices_for_user(user):
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
