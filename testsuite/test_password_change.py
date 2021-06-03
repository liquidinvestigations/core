from django.urls import reverse
from django.utils.timezone import now
from conftest import _totp, is_logged_in


def get_url():
    return reverse('password_change')


def payload_pw_change(oldpw, newpw1, newpw2, otp_token=None):
    payload = {
        'old_password': oldpw,
        'new_password1': newpw1,
        'new_password2': newpw2,
    }
    if otp_token:
        payload['otp_token'] = otp_token
    return payload


def test_password_change_no_totp(settings, client, create_user):
    settings.LIQUID_2FA = False
    client.login(username=create_user.user.get_username(),
                 password=create_user.password)
    resp = client.post(get_url(), payload_pw_change('badpassword',
                                                    'new_password',
                                                    'new_password'))
    assert not resp.context.get('form').is_valid()

    resp = client.post(get_url(), payload_pw_change(create_user.password,
                                                    'new_password',
                                                    'bad_new_password'))
    assert not resp.context.get('form').is_valid()

    resp = client.post(get_url(), payload_pw_change(create_user.password,
                                                    'new_password',
                                                    'new_password'))
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

    resp = client.post(get_url(), payload_pw_change(create_user.password,
                                                    'new_password',
                                                    'new_password',
                                                    999999))
    assert not resp.context.get('form').is_valid()

    device = create_device(user=create_user.user)

    resp = client.post(get_url(), payload_pw_change(create_user.password,
                                                    'new_password',
                                                    'new_password',
                                                    _totp(device, now())))
    client.logout()
    client.login(username=create_user.user.get_username(),
                 password=create_user.password)
    assert not is_logged_in(client)
    client.login(username=create_user.user.get_username(),
                 password='new_password')
    assert is_logged_in(client)
