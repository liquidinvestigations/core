from django.urls import reverse
from django.utils.timezone import now
from test_twofactor_invitation import _totp, _reset_last_use, is_logged_in


def test_password_change_no_totp(settings, client, test_user,
                                 test_user_name, test_user_pw):
    settings.LIQUID_2FA = False
    url = reverse('password_change')
    test_user()
    client.login(username=test_user_name, password=test_user_pw)
    client.post(url, {
        'old_password': test_user_pw,
        'new_password1': 'new_password',
        'new_password2': 'new_password',
    })
    client.logout()
    client.login(username=test_user_name, password='new_password')
    assert is_logged_in(client)


def test_password_change_totp(settings, client, test_user, test_user_name,
                              test_user_pw, test_device):
    url = reverse('password_change')
    user = test_user()
    device = test_device(user=user)
    _reset_last_use(device)
    client.login(username=test_user_name, password=test_user_pw)
    assert is_logged_in(client)
    client.post(url, {
        'old_password': test_user_pw,
        'new_password1': 'new_password',
        'new_password2': 'new_password',
        'otp_token': _totp(device, now())
    })
    client.logout()
    client.login(username=test_user_name, password='new_password')
    assert is_logged_in(client)
