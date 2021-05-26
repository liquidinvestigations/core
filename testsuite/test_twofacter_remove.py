from django.utils.timezone import now
from test_twofactor_invitation import _totp, _reset_last_use
import django_otp


def test_totp_remove(client, test_user, test_user_name,
                     test_user_pw, test_device):
    user = test_user()
    client.login(username=test_user_name, password=test_user_pw)
    _ = test_device(user=user)
    device2 = test_device(user=user, name='device2')
    _reset_last_use(device2)
    response = client.post('/accounts/totp/remove/', {
        'password': test_user_pw,
        'token': _totp(device2, now()),
        'device': device2.id,
    })
    assert response.context['success']
    totp_devices = django_otp.devices_for_user(user)
    totp_names = [device.name for device in totp_devices]
    assert 'device2' in totp_names
    assert 'device' not in totp_names
