import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

pytestmark = pytest.mark.django_db

WAN1 = {
  "static": {
    "ip": "192.168.66.66",
    "netmask": "255.255.255.0",
    "gateway": "192.168.66.1",
    "dns_server": "192.168.66.1"
  },
  "wifi": {
    "ssid": "network",
    "password": "password"
  }
}

WAN2 = {
  "wifi": {
    "ssid": "yet another network",
    "password": "yet another password"
  }
}

WAN_BROKEN = {
  "static": {
    "ip": "192.168.66.66",
    "netmask": "255.255.255.0",
    "gateway": "not an ip address",
    "dns_server": "192.168.66.1"
  },
  "wifi": {
    "ssid": "network",
    "password": "short"
  }
}

LAN1 = {
  "ip": "10.0.0.1",
  "netmask": "255.255.255.0",
  "dhcp_range": "10.0.0.100-255",
  "hotspot": {
    "ssid": "foo",
    "password": "barbaxqux"
  },
  "eth": False
}

LAN2 = {
  "ip": "192.168.0.1",
  "netmask": "255.255.0.0",
  "dhcp_range": "192.0.0.2-255",
  "hotspot": {
    "ssid": "yet another hotspot",
    "password": "more passwords!"
  },
  "eth": False
}

LAN_BROKEN = {
  "ip": "not an ip address",
  "netmask": "255.255.0.0",
  "dhcp_range": "192.0.0.2-255",
  "hotspot": {
    "ssid": "yet another hotspot",
    "password": "more passwords!"
  },
  "eth": False
}

SSH1 = {
  "enabled": True,
  "authorized_keys": [
    {"key": "key 1"},
    {"key": "key 2"},
    {"key": "key 3"}
  ],
  "port": 666
}

SSH2 = {
  "enabled": False,
  "authorized_keys": [],
  "port": 222
}

SSH_BROKEN = {
  "enabled": "whatever",
  "authorized_keys": [],
  "port": 222
}


REGISTRATION_DEFAULT = {
    "username": "admin",
    "password": "",
    "domain": "liquidnode.liquid",
    "lan": {
        "ip": "10.0.0.1",
        "netmask": "255.255.255.0",
        "dhcp_range": "10.0.0.100-255",
        "hotspot": {
            "ssid": "",
            "password": ""
        },
        "eth": False
    },
    "wan": {
        "wifi": {
            "ssid": "",
            "password": ""
        }
    },
    "ssh": {
        "enabled": False,
        "authorized_keys": [],
        "port": 22
    }
}

REGISTRATION1 =  {
    "username": "johnDoe",
    "password": "123b456x",
    "domain": "liquidnode.liquid",
    "lan": LAN1,
    "wan": WAN1,
    "ssh": SSH1
}

REGISTRATION2 =  {
    "username": "best_admin_user_ever",
    "password": "super secret password no one will ever guess",
    "domain": "mynode.liquidnode.liquid.node.com",
    "lan": LAN2,
    "wan": WAN2,
    "ssh": SSH2
}

@pytest.fixture
def client():
    return APIClient()

def check_get_response(client, endpoint, obj):
    get = client.get(endpoint)
    assert obj == get.json()
    assert 200 == get.status_code

def test_initial_registration_default(client):
    get = client.get('/api/registration/')
    assert 200 == get.status_code
    assert REGISTRATION_DEFAULT == get.json()

@pytest.mark.parametrize("data", [
    REGISTRATION1,
    REGISTRATION2,
])
def test_initial_registration_setup(client, data):
    post = client.post('/api/registration/', data=data, format='json')
    assert 200 == post.status_code

    # try to login
    assert client.login(username=data['username'], password=data['password'])

    # check the posted configs
    check_get_response(client, '/api/network/lan/', data['lan'])
    check_get_response(client, '/api/network/wan/', data['wan'])
    check_get_response(client, '/api/network/ssh/', data['ssh'])

    # post-registration, all calls to /api/registration should fail
    get = client.get('/api/registration/')
    assert 400 == get.status_code
    assert {'detail': "Registration already done"} == get.json()

    post = client.post('/api/registration/', data=data, format='json')
    assert 400 == post.status_code
    assert {'detail': "Registration already done"} == post.json()

@pytest.mark.parametrize("key,vals,broken_vals", [
    ("lan", [LAN1, LAN2], [LAN_BROKEN]),
    ("wan", [WAN1, WAN2], [WAN_BROKEN]),
    ("ssh", [SSH1, SSH2], [SSH_BROKEN]),
])
def test_network_configuration(client, key, vals, broken_vals):
    endpoint = '/api/network/{}/'.format(key)

    registration_post = client.post('/api/registration/',
                                    data=REGISTRATION1,
                                    format='json')
    assert 200 == registration_post.status_code
    assert client.login(username=REGISTRATION1['username'],
                        password=REGISTRATION1['password'])

    for val in vals:
        put = client.put(endpoint, data=val, format='json')
        assert 200 == put.status_code
        check_get_response(client, endpoint, val)

    for val in broken_vals:
        put = client.put(endpoint, data=val, format='json')
        assert 400 == put.status_code
        # check that the last successful update is still there
        check_get_response(client, endpoint, vals[-1])
