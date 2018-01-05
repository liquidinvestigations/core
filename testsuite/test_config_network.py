import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('mock_agent')]

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
  "ip": "10.103.0.1",
  "netmask": "255.255.255.0",
  "dhcp_range": "10.103.0.100,10.103.0.200,72h",
  "hotspot": {
    "ssid": "foo",
    "password": "barbaxqux"
  },
  "eth": True
}

LAN2 = {
  "ip": "192.168.0.1",
  "netmask": "255.255.0.0",
  "dhcp_range": "192.0.0.2,192.0.0.254,72h",
  "hotspot": {
    "ssid": "yet another hotspot",
    "password": "more passwords!"
  },
  "eth": False
}

LAN_BROKEN = {
  "ip": "not an ip address",
  "netmask": "255.255.0.0",
  "dhcp_range": "192.0.0.2,192.0.0.254,72h",
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
    "domain": "liquid.example.org",
    "lan": {
        "ip": "10.103.0.1",
        "netmask": "255.255.255.0",
        "dhcp_range": "10.103.0.100,10.103.0.200,72h",
        "hotspot": {
            "ssid": "",
            "password": ""
        },
        "eth": True
    },
    "wan": {
        "wifi": {
            "ssid": "",
            "password": ""
        }
    },
    "ssh": {
        "enabled": True,
        "authorized_keys": [],
        "port": 22
    }
}

REGISTRATION1 =  {
    "username": "johnDoe",
    "password": "123b456x",
    "domain": "liquid.example.org",
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
    assert get.status_code == 200

def test_initial_registration_default(client):
    get = client.get('/api/registration/')
    assert get.status_code == 200
    assert get.json() == REGISTRATION_DEFAULT

@pytest.mark.parametrize("data", [
    REGISTRATION1,
    REGISTRATION2,
])
def test_initial_registration_setup(client, data):
    post = client.post('/api/registration/', data=data, format='json')
    assert post.status_code == 200

    # try to login
    assert client.login(username=data['username'], password=data['password'])

    # check the posted configs
    check_get_response(client, '/api/network/lan/', data['lan'])
    check_get_response(client, '/api/network/wan/', data['wan'])
    check_get_response(client, '/api/network/ssh/', data['ssh'])

    # post-registration, all calls to /api/registration should fail
    get = client.get('/api/registration/')
    assert get.status_code == 400
    assert get.json() == {'detail': "Registration already done"}

    post = client.post('/api/registration/', data=data, format='json')
    assert post.status_code == 400
    assert post.json() == {'detail': "Registration already done"}

GOOD_DOMAINS = [{'domain': d} for d in [
    'liquidnode.local',
    'however-bored-ill-write-tests.com',
    'more.segments.please.org',
    'some-dashes.auto',
    'weird-tld.liquid',
    'num8berx.zero',
]]

BAD_DOMAINS = [{'domain': d} for d in [
    'under_score.com',
    'other~things.xxx',
    'dash-where-it.shouldnt-be',
    'put+both-patches.cn',
]]

@pytest.mark.parametrize("endpoint,vals,broken_vals", [
    ("/api/network/lan/", [LAN1, LAN2], [LAN_BROKEN]),
    ("/api/network/wan/", [WAN1, WAN2], [WAN_BROKEN]),
    ("/api/network/ssh/", [SSH1, SSH2], [SSH_BROKEN]),
])
def test_network_configuration(client, endpoint, vals, broken_vals):
    registration_post = client.post('/api/registration/',
                                    data=REGISTRATION1,
                                    format='json')
    assert registration_post.status_code == 200
    assert client.login(username=REGISTRATION1['username'],
                        password=REGISTRATION1['password'])

    for val in vals:
        put = client.put(endpoint, data=val, format='json')
        assert put.status_code == 200
        check_get_response(client, endpoint, val)

    for val in broken_vals:
        put = client.put(endpoint, data=val, format='json')
        assert put.status_code == 400
        # check that the last successful update is still there
        check_get_response(client, endpoint, vals[-1])

@pytest.mark.parametrize("vals,broken_vals", [
    (GOOD_DOMAINS, BAD_DOMAINS),
])
def test_network_configuration_domain_immutable(client, vals, broken_vals):
    registration_post = client.post('/api/registration/',
                                    data=REGISTRATION1,
                                    format='json')
    assert registration_post.status_code == 200
    assert client.login(username=REGISTRATION1['username'],
                        password=REGISTRATION1['password'])

    for val in vals:
        put = client.put("/api/network/domain/", data=val, format='json')
        assert put.status_code == 405

    for val in broken_vals:
        put = client.put("/api/network/domain/", data=val, format='json')
        assert put.status_code == 405

    domain = client.get("/api/network/domain/")
    assert domain.status_code == 200
    assert domain.json() == {"domain": REGISTRATION1["domain"]}
