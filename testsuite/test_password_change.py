from django.urls import reverse
from django.utils.timezone import now
from conftest import _totp, is_logged_in


def test_password_change_no_totp(settings, client, create_user):
    settings.LIQUID_2FA = False
    url = reverse('password_change')
    client.login(username=create_user['user'].get_username(),
                 password=create_user['password'])
    client.post(url, {
        'old_password': create_user['password'],
        'new_password1': 'new_password',
        'new_password2': 'new_password',
    })
    client.logout()
    client.login(username=create_user['user'].get_username(),
                 password='new_password')
    assert is_logged_in(client)


def test_password_change_totp(settings, client, create_user, create_device):
    url = reverse('password_change')
    device = create_device(user=create_user['user'])
    client.login(username=create_user['user'],
                 password=create_user['password'])
    assert is_logged_in(client)
    client.post(url, {
        'old_password': create_user['password'],
        'new_password1': 'new_password',
        'new_password2': 'new_password',
        'otp_token': _totp(device, now())
    })
    client.logout()
    client.login(username=create_user['user'].get_username(),
                 password='new_password')
    assert is_logged_in(client)
