from django.utils.timezone import now
from test_twofactor_invitation import _totp, _reset_last_use
import django_otp


def test_totp_remove(client, test_user, test_device):
    user = test_user()
    client.login(username=user['username'], password=user['password'])
    test_device(user=user['user'])
    device2 = test_device(user=user['user'], name='device2')
    _reset_last_use(device2)
    response = client.post('/accounts/totp/remove/', {
        'password': user['password'],
        'token': _totp(device2, now()),
        'device': device2.id,
    })
    assert response.context['success']
    totp_names = [device.name
                  for device
                  in django_otp.devices_for_user(user['user'])]
    assert 'device2' in totp_names
    assert 'device' not in totp_names
