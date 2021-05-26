from django.utils.timezone import now
from test_twofactor_invitation import _totp, _reset_last_use
from django_otp.plugins.otp_totp.models import TOTPDevice
import django_otp


def test_totp_add(client, test_user, test_device):
    user = test_user()
    client.login(username=user['username'], password=user['password'])
    device = test_device(user=user['user'])
    _reset_last_use(device)
    response = client.post('/accounts/totp/add/', {
        'password': user['password'],
        'token': _totp(device, now()),
        'new_name': 'new_device_name',
    })
    assert response.url == '/accounts/totp/confirm/'
    assert sum(1 for device in django_otp.devices_for_user(user['user'])) == 2
    new_device = (TOTPDevice.objects
                  .devices_for_user(user['user']).get(name='new_device_name'))
    _reset_last_use(device)
    confirm_response = client.post('/accounts/totp/confirm/', {
        'new_token': _totp(new_device, now()),
    })
    assert confirm_response.context['success']
