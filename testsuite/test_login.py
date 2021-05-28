import pytest
from django.urls import reverse
from django.utils.timezone import now
from conftest import _totp, is_logged_in

pytestmark = pytest.mark.django_db


def get_url():
    return reverse('login')


def test_login_page_no_totp(client, settings):
    settings.LIQUID_2FA = False
    resp = client.get(get_url())
    assert resp.status_code == 200


def test_login_page(client):
    resp = client.get(get_url())
    assert resp.status_code == 200


def test_login_no_totp(client, settings, create_user):
    settings.LIQUID_2FA = False
    client.post(get_url(), {
        'username': create_user['user'].get_username(),
        'password': create_user['password'],
    })
    assert is_logged_in(client)
    client.logout()
    assert not is_logged_in(client)

    client.post(get_url(), {
        'username': 'badusername',
        'password': create_user['password'],
    })
    assert not is_logged_in(client)

    client.post(get_url(), {
        'username': create_user['user'].get_username(),
        'password': 'badusername',
    })
    assert not is_logged_in(client)


def test_login_totp(client, create_user, create_device):
    device = create_device(user=create_user['user'])
    client.post(get_url(), {
        'username': create_user['user'].get_username(),
        'password': create_user['password'],
        'otp_token': _totp(device, now())
    })
    assert is_logged_in(client)
    client.logout()
    assert not is_logged_in(client)


def test_homepage(client, create_user):
    url = reverse('home')
    resp = client.get(url)
    assert resp.status_code == 302
    client.login(username=create_user['user'].get_username(),
                 password=create_user['password'])
    resp = client.get('')
    assert resp.status_code == 200