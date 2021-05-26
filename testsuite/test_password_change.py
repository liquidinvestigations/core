from django.urls import reverse
from django.utils.timezone import now
from test_twofactor_invitation import _totp, _reset_last_use, is_logged_in


def test_password_change_no_totp(settings, client, test_user):
    settings.LIQUID_2FA = False
    url = reverse('password_change')
    user = test_user()
    client.login(username=user['username'], password=user['password'])
    client.post(url, {
        'old_password': user['password'],
        'new_password1': 'new_password',
        'new_password2': 'new_password',
    })
    client.logout()
    client.login(username=user['username'], password='new_password')
    assert is_logged_in(client)


def test_password_change_totp(settings, client, test_user, test_device):
    url = reverse('password_change')
    user = test_user()
    device = test_device(user=user['user'])
    _reset_last_use(device)
    client.login(username=user['username'], password=user['password'])
    assert is_logged_in(client)
    client.post(url, {
        'old_password': user['password'],
        'new_password1': 'new_password',
        'new_password2': 'new_password',
        'otp_token': _totp(device, now())
    })
    client.logout()
    client.login(username=user['username'], password='new_password')
    assert is_logged_in(client)
