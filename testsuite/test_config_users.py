import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

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

def test_get_users(client, admin_user):
    assert client.login(username='admin', password='q')

    users_resp = client.get('/api/users/')
    assert users_resp.status_code == 200
    assert [u['username'] for u in users_resp.json()] == ['admin']

def test_create_users(client, admin_user):
    assert client.login(username='admin', password='q')

    create = client.post('/api/users/', data={
        "username": "mike",
        "is_admin": False,
        "first_name": "Mike",
        "last_name": "Tyson",
        "is_active": True,
    })
    assert create.status_code == 201

    user_list = client.get("/api/users/")
    assert set(u['username'] for u in user_list.json()) == set(["admin", "mike"])

    get_mike = client.get('/api/users/mike/')
    assert get_mike.status_code == 200
    assert "mike" == get_mike.json()['username']
    assert False == get_mike.json()['is_admin']
    assert "Mike" == get_mike.json()['first_name']
    assert "Tyson" == get_mike.json()['last_name']
    assert True == get_mike.json()['is_active']

def test_password_change_admin_self(client, admin_user):
    assert client.login(username='admin', password='q')

    # test invalidation of short password
    password = client.post("/api/users/admin/password/", data={
        "new_password": "qqq",
    })
    assert password.status_code == 400
    assert password.json() == {"new_password": ["password too short"]}

    # make sure old password still works
    client.logout()
    assert client.login(username='admin', password='q')

    # change the password
    password = client.post("/api/users/admin/password/", data={
        "new_password": "12345678",
    })
    assert password.status_code == 200

    # make sure new login works
    client.logout()
    client.login(username='admin', password='12345678')

def test_password_change_nonadmin(client):
    User.objects.create_user(
        username='mike',
        password='mike',
        is_staff=False
    )

    assert client.login(username='mike', password='mike')

    # change the password without giving out the old one
    password = client.post("/api/users/mike/password/", data={
        "new_password": "12345678",
    })
    assert password.status_code == 400
    assert "old_password not specified" == password.json()['detail']

    # change the password by giving a wrong old one
    password = client.post("/api/users/mike/password/", data={
        "old_password": "bad password over here",
        "new_password": "12345678",
    })
    assert password.status_code == 400
    assert "Wrong Password" == password.json()['old_password'][0]

    # change the password properly
    password = client.post("/api/users/mike/password/", data={
        "old_password": "mike",
        "new_password": "12345678",
    })
    assert password.status_code == 200

    # check new login
    client.logout()
    assert client.login(username='mike', password='12345678')

def test_set_users_active(client, admin_user):
    assert client.login(username='admin', password='q')

    create = client.post('/api/users/', data={
        "username": "mike",
        "is_admin": False,
        "first_name": "Mike",
        "last_name": "Tyson",
        "is_active": True,
    })
    assert create.status_code == 201

    # make sure the user is active
    get_mike = client.get('/api/users/mike/')
    assert get_mike.status_code == 200
    assert True == get_mike.json()['is_active']

    # set mike as inactive
    set_inactive_mike = client.put('/api/users/mike/active/', data={
        'is_active': False
    })
    assert set_inactive_mike.status_code == 200
    get_mike = client.get('/api/users/mike/')
    assert get_mike.status_code == 200
    assert False == get_mike.json()['is_active']

    # set mike as active again
    set_active_mike = client.put('/api/users/mike/active/', data={
        'is_active': True
    })
    assert set_active_mike.status_code == 200
    get_mike = client.get('/api/users/mike/')
    assert get_mike.status_code == 200
    assert True == get_mike.json()['is_active']

    # set a password for mike for us to log on to
    password = client.post("/api/users/mike/password/", data={
        "new_password": "12345678",
    })
    assert password.status_code == 200

    # test that mike can't hit /api/$user/active/
    client.logout()
    client.login(username='mike', password='12345678')
    set_inactive_mike = client.put('/api/users/mike/active/', data={
        'is_active': False
    })
    assert set_inactive_mike.status_code == 403
