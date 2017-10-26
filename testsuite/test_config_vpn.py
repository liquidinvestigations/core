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
    assert vpn_status.status_code == 200

    client_status = vpn_status.json()['client']
    assert client_status['state_description'] == "Disabled."
    assert client_status['is_enabled'] == False
    assert client_status['is_running'] == False
    assert client_status['error_message'] == None

    server_status = vpn_status.json()['server']
    assert server_status['state_description'] == "Disabled."
    assert server_status['is_enabled'] == False
    assert server_status['is_running'] == False
    assert server_status['error_message'] == None
    assert server_status['registered_key_count'] == 0
    assert server_status['active_connection_count'] == 0

def test_vpn_server_enable_disable(client):
    server_enable = client.put('/api/vpn/server/', data={
        'is_enabled': True,
    })
    assert server_enable.status_code == 200
    assert client.get('/api/vpn/').json()['server']['is_enabled'] == True

    server_disable = client.put('/api/vpn/server/', data={
        'is_enabled': False,
    })
    assert server_enable.status_code == 200
    assert client.get('/api/vpn/').json()['server']['is_enabled'] == False

def test_vpn_client_enable_disable(client):
    client_enable = client.put('/api/vpn/client/', data={
        'is_enabled': True,
    })
    assert client_enable.status_code == 200
    assert client.get('/api/vpn/').json()['client']['is_enabled'] == True

    client_disable = client.put('/api/vpn/client/', data={
        'is_enabled': False,
    })
    assert client_enable.status_code == 200
    assert client.get('/api/vpn/').json()['client']['is_enabled'] == False

def test_vpn_server_generate_client_key(client):
    EXPECTED_FIRST_KEY = {'id': 1, 'label': 'xxx', 'revoked': False}
    EXPECTED_SECOND_KEY = {'id': 2, 'label': 'yyy', 'revoked': False}
    # test that initially, the list is empty
    client_key_list = client.get('/api/vpn/server/keys/')
    assert client_key_list.status_code == 200
    assert client_key_list.json() == []

    # generate a key
    generate = client.post('/api/vpn/server/keys/generate/', data={
        'label': EXPECTED_FIRST_KEY['label'],
    })
    assert generate.status_code == 200
    assert generate.json() == EXPECTED_FIRST_KEY

    # test that it's in the list
    client_key_list = client.get('/api/vpn/server/keys/')
    assert client_key_list.status_code == 200
    [first_key] = client_key_list.json()
    assert first_key == EXPECTED_FIRST_KEY
    assert first_key == client.get('/api/vpn/server/keys/1/').json()

    # generate a second key
    generate = client.post('/api/vpn/server/keys/generate/', data={
        'label': EXPECTED_SECOND_KEY['label'],
    })
    assert generate.status_code == 200
    assert generate.json() == EXPECTED_SECOND_KEY
    client_key_list = client.get('/api/vpn/server/keys/')
    assert client_key_list.status_code == 200
    [first_key, second_key] = client_key_list.json()
    assert first_key == EXPECTED_FIRST_KEY
    assert second_key == EXPECTED_SECOND_KEY

def test_vpn_server_revoke_client_key(client):
    generate = client.post('/api/vpn/server/keys/generate/', data={
        'label': 'xxx',
    })
    assert generate.status_code == 200

    revoke = client.post('/api/vpn/server/keys/1/revoke/', data={
        'revoked_reason': 'yyy',
    })
    assert revoke.status_code == 200
    get_revoked = client.get('/api/vpn/server/keys/1/')
    assert get_revoked.status_code == 200
    revoked_key = get_revoked.json()
    assert revoked_key['id'] == 1
    assert revoked_key['label'] == 'xxx'
    assert revoked_key['revoked'] == True
    assert revoked_key['revoked_by'] == 'admin'
    assert revoked_key['revoked_at']
    assert revoked_key['revoked_reason'] == 'yyy'

def test_vpn_server_download_client_keys(client):
    generate = client.post('/api/vpn/server/keys/generate/', data={
        'label': 'xxx',
    })
    assert generate.status_code == 200

    download = client.get('/api/vpn/server/keys/1/download/')
    assert download.status_code == 200
    assert download['Content-Type'] == OVPN_CONTENT_TYPE

def test_vpn_client_upload_ovpn(client):
    OVPN_CONTENT = 'dummy ovpn file content'
    upload = client.post('/api/vpn/client/upload/',
        data=OVPN_CONTENT,
        content_type=OVPN_CONTENT_TYPE
    )
    assert upload.status_code == 200
