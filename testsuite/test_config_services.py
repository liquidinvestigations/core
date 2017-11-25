import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('mock_agent')]

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username='admin',
        password='q',
        is_staff=True,
    )

SERVICES = [
    'hoover',
    'hypothesis',
    'matrix',
    'dokuwiki',
    'davros',
]

def test_get_services(client, admin_user):
    assert client.login(username='admin', password='q')

    get_service_list = client.get('/api/services/')
    assert get_service_list.status_code == 200
    assert set(s['name'] for s in get_service_list.json()) == set(SERVICES)

@pytest.mark.parametrize("app_name", SERVICES)
def test_set_service_enabled(client, admin_user, app_name):
    assert client.login(username='admin', password='q')
    enabled_endpoint = '/api/services/{}/enabled/'.format(app_name)
    get_endpoint = '/api/services/{}/'.format(app_name)

    for is_enabled in True, False:
        put = client.put(enabled_endpoint, data={'is_enabled': is_enabled})
        assert put.status_code == 200

        get = client.get(get_endpoint)
        assert get.status_code == 200
        assert get.json()['is_enabled'] == is_enabled

def test_service_permissions(client):
    app_name = SERVICES[0]
    enabled_endpoint = '/api/services/{}/enabled/'.format(app_name)
    get_endpoint = '/api/services/{}/'.format(app_name)

    # try to get/put without being logged in
    get = client.get(get_endpoint)
    assert get.status_code == 403
    put = client.put(enabled_endpoint, data={'is_enabled': False})
    assert put.status_code == 403

    # make a normal user and login
    User.objects.create_user(
        username='mick',
        password='mick',
        is_staff=False,
    )
    assert client.login(username='mick', password='mick')

    # try to get/put without admin rights
    get = client.get(get_endpoint)
    assert get.status_code == 200
    put = client.put(enabled_endpoint, data={'is_enabled': False})
    assert put.status_code == 403
