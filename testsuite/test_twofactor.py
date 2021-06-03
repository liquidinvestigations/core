from django.utils.timezone import now
from conftest import _totp
import django_otp
from liquidcore.twofactor.models import TOTPDeviceTimed
from django.urls import reverse


def get_rm_url():
    return reverse('totp_remove')


def get_add_url():
    return reverse('totp_add')


def get_change_url():
    return reverse('totp_change')


def user_device_count(user):
    return len(list(TOTPDeviceTimed.objects.devices_for_user(user)))


def test_totp_remove(client, create_user, create_device):
    client.login(username=create_user.user.get_username(),
                 password=create_user.password)
    create_device(user=create_user.user)
    device2 = create_device(user=create_user.user, name='device2')
    response = client.post(get_rm_url(), {
        'password': create_user.password,
        'token': _totp(device2, now()),
    })
    assert response.context['success']
    totp_names = [device.name
                  for device
                  in django_otp.devices_for_user(create_user.user)]
    assert 'device2' in totp_names
    assert 'device' not in totp_names


def test_totp_add(client, create_user, create_device):
    client.login(username=create_user.user.get_username(),
                 password=create_user.password)
    device = create_device(user=create_user.user)
    response = client.post(get_add_url(), {
        'password': create_user.password,
        'token': _totp(device, now()),
        'new_name': 'new_device_name',
    })
    assert response.context['otp_png']
    new_device = (TOTPDeviceTimed.objects
                  .devices_for_user(create_user.user)
                  .get(name='new_device_name'))
    confirm_response = client.post(get_add_url(), {
        'new_token': _totp(new_device, now()),
    })
    assert confirm_response.context['confirmed']
    assert user_device_count(create_user.user) == 2


def test_totp_change(client, create_user, create_device):
    client.login(username=create_user.user.get_username(),
                 password=create_user.password)
    device = create_device(user=create_user.user)
    response = client.post(get_change_url(), {
        'password': create_user.password,
        'token': _totp(device, now()),
        'new_name': 'new_device_name',
    })
    assert response.context['otp_png']
    new_device = (TOTPDeviceTimed.objects
                  .devices_for_user(create_user.user)
                  .get(name='new_device_name'))
    confirm_response = client.post(get_change_url(), {
        'new_token': _totp(new_device, now()),
    })
    assert confirm_response.context['confirmed']
    assert user_device_count(create_user.user) == 1
