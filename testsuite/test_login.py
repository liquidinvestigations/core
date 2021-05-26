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


def test_login_no_totp(client, settings, test_user):
    settings.LIQUID_2FA = False
    user = test_user()
    client.post('/accounts/login/', {
        'username': user['username'],
        'password': user['password'],
    })
    assert is_logged_in(client)
    client.logout()
    assert not is_logged_in(client)


def test_login_totp(client, test_user, test_device):
    user = test_user()
    device = test_device(user=user['user'])
    _reset_last_use(device)
    client.post('/accounts/login/', {
        'username': user['username'],
        'password': user['password'],
        'otp_token': _totp(device, now())
    })
    assert is_logged_in(client)
    client.logout()
    assert not is_logged_in(client)


def test_homepage(client, test_user):
    resp = client.get('')
    assert resp.status_code == 302
    user = test_user()
    client.login(username=user['username'], password=user['password'])
    resp = client.get('')
    assert resp.status_code == 200
