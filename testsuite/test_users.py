import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

pytestmark = pytest.mark.django_db

@pytest.fixture
def client():
    return APIClient()

def test_get_users(client):
    User.objects.create_user(username='admin', password='q', is_staff=True)
    assert client.login(username='admin', password='q')

    users_resp = client.get('/api/users/')
    assert users_resp.status_code == 200
    assert [u['username'] for u in users_resp.json()] == ['admin']
