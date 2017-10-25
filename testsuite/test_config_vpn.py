import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from liquidcore.config.models import VPNClientKey

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('mock_agent')]

@pytest.fixture
def client():
    USERNAME = 'admin'
    PASSWORD = 'q' * 20
    User.objects.create_user(
        username=USERNAME,
        password=PASSWORD,
        is_staff=True,
    )
    api_client = APIClient()
    assert api_client.login(username=USERNAME, password=PASSWORD)
    return api_client

OVPN_CONTENT_TYPE = 'application/x-openvpn-profile'

def test_vpn_system_status(client):
    vpn_status = client.get('/api/vpn/')
    assert 200 == vpn_status.status_code

    client_status = vpn_status.json()['client']
    assert "Disabled." == client_status['state_description']
    assert False == client_status['is_enabled']
    assert False == client_status['is_running']
    assert None == client_status['error_message']

    server_status = vpn_status.json()['server']
    assert "Disabled." == server_status['state_description']
    assert False == server_status['is_enabled']
    assert False == server_status['is_running']
    assert None == server_status['error_message']
    assert 0 == server_status['registered_key_count']
    assert 0 == server_status['active_connection_count']

def test_vpn_server_enable_disable(client):
    server_enable = client.put('/api/vpn/server/', data={
        'is_enabled': True,
    })
    assert 200 == server_enable.status_code
    assert True == client.get('/api/vpn/').json()['server']['is_enabled']

    server_disable = client.put('/api/vpn/server/', data={
        'is_enabled': False,
    })
    assert 200 == server_enable.status_code
    assert False == client.get('/api/vpn/').json()['server']['is_enabled']

def test_vpn_client_enable_disable(client):
    client_enable = client.put('/api/vpn/client/', data={
        'is_enabled': True,
    })
    assert 200 == client_enable.status_code
    assert True == client.get('/api/vpn/').json()['client']['is_enabled']

    client_disable = client.put('/api/vpn/client/', data={
        'is_enabled': False,
    })
    assert 200 == client_enable.status_code
    assert False == client.get('/api/vpn/').json()['client']['is_enabled']

def test_vpn_server_generate_client_key(client):
    EXPECTED_FIRST_KEY = {'id': 1, 'label': 'xxx', 'revoked': False}
    EXPECTED_SECOND_KEY = {'id': 2, 'label': 'yyy', 'revoked': False}
    # test that initially, the list is empty
    client_key_list = client.get('/api/vpn/server/keys/')
    assert 200 == client_key_list.status_code
    assert [] == client_key_list.json()

    # generate a key
    generate = client.post('/api/vpn/server/keys/generate/', data={
        'label': EXPECTED_FIRST_KEY['label'],
    })
    assert 200 == generate.status_code
    assert generate.json() == EXPECTED_FIRST_KEY

    # test that it's in the list
    client_key_list = client.get('/api/vpn/server/keys/')
    assert 200 == client_key_list.status_code
    [first_key] = client_key_list.json()
    assert first_key == EXPECTED_FIRST_KEY
    assert first_key == client.get('/api/vpn/server/keys/1/').json()

    # generate a second key
    generate = client.post('/api/vpn/server/keys/generate/', data={
        'label': EXPECTED_SECOND_KEY['label'],
    })
    assert 200 == generate.status_code
    assert generate.json() == EXPECTED_SECOND_KEY
    client_key_list = client.get('/api/vpn/server/keys/')
    assert 200 == client_key_list.status_code
    [first_key, second_key] = client_key_list.json()
    assert first_key == EXPECTED_FIRST_KEY
    assert second_key == EXPECTED_SECOND_KEY

def test_vpn_server_revoke_client_key(client):
    generate = client.post('/api/vpn/server/keys/generate/', data={
        'label': 'xxx',
    })
    assert 200 == generate.status_code

    revoke = client.post('/api/vpn/server/keys/1/revoke/', data={
        'revoked_reason': 'yyy',
    })
    assert 200 == revoke.status_code
    get_revoked = client.get('/api/vpn/server/keys/1/')
    assert 200 == get_revoked.status_code
    revoked_key = get_revoked.json()
    assert 1 == revoked_key['id']
    assert 'xxx' == revoked_key['label']
    assert True == revoked_key['revoked']
    assert 'admin' == revoked_key['revoked_by']
    assert revoked_key['revoked_at']
    assert 'yyy' == revoked_key['revoked_reason']

def test_vpn_server_download_client_keys(client):
    generate = client.post('/api/vpn/server/keys/generate/', data={
        'label': 'xxx',
    })
    assert 200 == generate.status_code

    download = client.get('/api/vpn/server/keys/1/download/')
    assert 200 == download.status_code
    assert OVPN_CONTENT_TYPE == download['Content-Type']

def test_vpn_client_upload_ovpn(client):
    OVPN_CONTENT = 'dummy ovpn file content'
    upload = client.post('/api/vpn/client/upload/',
        data=OVPN_CONTENT,
        content_type=OVPN_CONTENT_TYPE
    )
    assert 200 == upload.status_code
