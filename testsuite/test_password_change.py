from django.urls import reverse
from django.utils.timezone import now
from conftest import _totp, is_logged_in


def get_url():
    return reverse('password_change')


def test_password_change_no_totp(settings, client, create_user):
    settings.LIQUID_2FA = False
    client.login(username=create_user.user.get_username(),
                 password=create_user.password)
    resp = client.post(get_url(), {
        'old_password': 'badpassword',
        'new_password1': 'new_password',
        'new_password2': 'new_password',
    })
    assert not resp.context.get('form').is_valid()

    resp = client.post(get_url(), {
        'old_password': create_user.password,
        'new_password1': 'new_password',
        'new_password2': 'bad_new_password',
    })
    assert not resp.context.get('form').is_valid()

    client.post(get_url(), {
        'old_password': create_user.password,
        'new_password1': 'new_password',
        'new_password2': 'new_password',
    })
    client.logout()
    client.login(username=create_user.user.get_username(),
                 password=create_user.password)
    assert not is_logged_in(client)
    client.login(username=create_user.user.get_username(),
                 password='new_password')
    assert is_logged_in(client)


def test_password_change_totp(settings, client, create_user, create_device):
    client.login(username=create_user.user.get_username(),
                 password=create_user.password)
    assert is_logged_in(client)

    resp = client.post(get_url(), {
        'old_password': create_user.password,
        'new_password1': 'new_password',
        'new_password2': 'new_password',
        'otp_token': 999999,
    })
    assert not resp.context.get('form').is_valid()

    device = create_device(user=create_user.user)
    resp = client.post(get_url(), {
        'old_password': create_user.password,
        'new_password1': 'new_password',
        'new_password2': 'new_password',
        'otp_token': _totp(device, now())
    })
    client.logout()
    client.login(username=create_user.user.get_username(),
                 password=create_user.password)
    assert not is_logged_in(client)
    client.login(username=create_user.user.get_username(),
                 password='new_password')
    assert is_logged_in(client)
