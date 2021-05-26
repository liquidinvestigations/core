import pytest
from django.urls import reverse
from django.utils.timezone import now
from test_twofactor_invitation import _totp, _reset_last_use, is_logged_in

pytestmark = pytest.mark.django_db


def test_login_page_no_totp(client, settings):
    settings.LIQUID_2FA = False
    url = reverse('login')
    resp = client.get(url)
    assert resp.status_code == 200


def test_login_page(client):
    url = reverse('login')
    resp = client.get(url)
    assert resp.status_code == 200


def test_login_no_totp(client, settings, test_user,
                       test_user_name, test_user_pw):
    settings.LIQUID_2FA = False
    test_user()
    client.post('/accounts/login/', {
        'username': test_user_name,
        'password': test_user_pw,
    })
    assert is_logged_in(client)
    client.logout()
    assert not is_logged_in(client)


def test_login_totp(client, test_user, test_device,
                    test_user_name, test_user_pw):
    user = test_user()
    device = test_device(user=user)
    _reset_last_use(device)
    client.post('/accounts/login/', {
        'username': test_user_name,
        'password': test_user_pw,
        'otp_token': _totp(device, now())
    })
    assert is_logged_in(client)
    client.logout()
    assert not is_logged_in(client)


def test_homepage(client, test_user, test_user_name, test_user_pw):
    resp = client.get('')
    assert resp.status_code == 302
    test_user()
    client.login(username=test_user_name, password=test_user_pw)
    resp = client.get('')
    assert resp.status_code == 200
