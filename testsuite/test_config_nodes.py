import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from liquidcore.config.models import Node

pytestmark = pytest.mark.django_db

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

@pytest.fixture
def example_node():
    node = Node(
        name='first.node',
        trusted=False,
        address='192.168.0.123',
    )
    node.data = {
        "address": "102.168.0.123",
        "discovery_interface": "interface",
        "last_seen_at": "date",
        "discovered_at": "date"
    }
    node.save()
    return node

SERIALIZED_NODE = {
    'data': {
        'address': '102.168.0.123',
        'discovered_at': 'date',
        'discovery_interface': 'interface',
        'last_seen_at': 'date'
    },
    'id': 1,
    'is_trusted': False,
    'hostname': 'first.node'
}

def test_get_nodes(client, admin_user, example_node):
    assert client.login(username='admin', password='q')

    users_resp = client.get('/api/nodes/')
    assert 200 == users_resp.status_code
    assert [SERIALIZED_NODE] == users_resp.json()
