from django.utils.timezone import now
from conftest import _totp
import django_otp
from django_otp.plugins.otp_totp.models import TOTPDevice


REMOVE_URL = '/accounts/totp/remove/'
ADD_URL = '/accounts/totp/add/'
CONFIRM_URL = '/accounts/totp/confirm/'
CHANGE_URL = '/accounts/totp/change/'


def user_device_count(user):
    return len(list(django_otp.devices_for_user(user)))


def test_totp_remove(client, create_user, create_device):
    client.login(username=create_user['user'].get_username(),
                 password=create_user['password'])
    create_device(user=create_user['user'])
    device2 = create_device(user=create_user['user'], name='device2')
    response = client.post(REMOVE_URL, {
        'password': create_user['password'],
        'token': _totp(device2, now()),
        'device': device2.id,
    })
    assert response.context['success']
    totp_names = [device.name
                  for device
                  in django_otp.devices_for_user(create_user['user'])]
    assert 'device2' in totp_names
    assert 'device' not in totp_names


def test_totp_add(client, create_user, create_device):
    client.login(username=create_user['user'].get_username(),
                 password=create_user['password'])
    device = create_device(user=create_user['user'])
    response = client.post(ADD_URL, {
        'password': create_user['password'],
        'token': _totp(device, now()),
        'new_name': 'new_device_name',
    })
    assert response.url == CONFIRM_URL
    assert user_device_count(create_user['user']) == 2
    new_device = (TOTPDevice.objects
                  .devices_for_user(create_user['user'])
                  .get(name='new_device_name'))
    confirm_response = client.post(CONFIRM_URL, {
        'new_token': _totp(new_device, now()),
    })
    assert confirm_response.context['success']


def test_totp_change(client, create_user, create_device):
    client.login(username=create_user['user'].get_username(),
                 password=create_user['password'])
    device = create_device(user=create_user['user'])
    response = client.post(CHANGE_URL, {
        'password': create_user['password'],
        'token': _totp(device, now()),
        'new_name': 'new_device_name',
    })
    assert response.url == CONFIRM_URL
    assert user_device_count(create_user['user']) == 2
    new_device = (TOTPDevice.objects
                  .devices_for_user(create_user['user']).get(name='new_device_name'))
    confirm_response = client.post(CONFIRM_URL, {
        'new_token': _totp(new_device, now()),
    })
    assert confirm_response.context['success']
    assert user_device_count(create_user['user']) == 1
