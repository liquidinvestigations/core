from django_otp.plugins.otp_totp.models import TOTPDevice
from django.utils.timezone import now
from test_twofactor_invitation import _totp, _reset_last_use
import django_otp


def test_totp_change(client, test_user, test_user_name,
                     test_user_pw, test_device):
    user = test_user()
    client.login(username=test_user_name, password=test_user_pw)
    device = test_device(user=user)
    _reset_last_use(device)
    response = client.post('/accounts/totp/change/', {
        'password': test_user_pw,
        'token': _totp(device, now()),
        'new_name': 'new_device_name',
    })
    assert response.url == '/accounts/totp/confirm/'
    totp_devices = django_otp.devices_for_user(user)
    assert len(list(totp_devices)) == 2
    new_device = (TOTPDevice.objects
                  .devices_for_user(user).get(name='new_device_name'))
    _reset_last_use(device)
    confirm_response = client.post('/accounts/totp/confirm/', {
        'new_token': _totp(new_device, now()),
    })
    assert confirm_response.context['success']
    totp_devices_new = django_otp.devices_for_user(user)
    assert len(list(totp_devices_new)) == 1
