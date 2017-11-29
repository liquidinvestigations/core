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
        "password": "1234567890",
        "is_admin": False,
        "first_name": "Mike",
        "last_name": "Tyson",
        "is_active": True,
    })
    assert create.status_code == 201
    assert 'password' not in create.json()

    user_list = client.get("/api/users/")
    assert set(u['username'] for u in user_list.json()) == set(["admin", "mike"])

    get_mike = client.get('/api/users/mike/')
    assert get_mike.status_code == 200
    assert get_mike.json()['username'] == "mike"
    assert get_mike.json()['is_admin'] == False
    assert get_mike.json()['first_name'] == "Mike"
    assert get_mike.json()['last_name'] == "Tyson"
    assert get_mike.json()['is_active'] == True

    mike = User.objects.get(username='mike')
    assert mike.check_password('1234567890')

def test_admins_cant_change_username(client, admin_user):
    assert client.login(username='admin', password='q')

    User.objects.create_user(
        username='mike',
        password='mike',
        is_staff=False
    )

    change_username = client.put("/api/users/mike/", data={
        "username": "mickey",
    })
    assert change_username.status_code == 400

    # make sure nothing has changed
    user_list = client.get("/api/users/")
    assert set(u['username'] for u in user_list.json()) == set(["admin", "mike"])

    get_mike = client.get('/api/users/mike/')
    assert get_mike.status_code == 200
    assert get_mike.json()['username'] == "mike"

def test_users_cant_change_username(client, admin_user):
    User.objects.create_user(
        username='mike',
        password='mike',
        is_staff=False
    )
    assert client.login(username='mike', password='mike')

    change_username = client.put("/api/users/mike/", data={
        "username": "mickey",
    })
    assert change_username.status_code == 403
    client.logout()

    # make sure nothing has changed
    assert client.login(username='admin', password='q')
    user_list = client.get("/api/users/")
    assert set(u['username'] for u in user_list.json()) == set(["admin", "mike"])

    get_mike = client.get('/api/users/mike/')
    assert get_mike.status_code == 200
    assert get_mike.json()['username'] == "mike"

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
    assert client.login(username='admin', password='12345678')

def test_password_change_nonadmin(client):
    User.objects.create_user(
        username='mike',
        password='mike',
        is_staff=False
    )

    User.objects.create_user(
        username='joe',
        password='joe',
        is_staff=False
    )

    assert client.login(username='mike', password='mike')

    # change the password without giving out the old one
    password = client.post("/api/users/mike/password/", data={
        "new_password": "12345678",
    })
    assert password.status_code == 400
    assert password.json()['detail'] == "old_password not specified"

    # change the password by giving a wrong old one
    password = client.post("/api/users/mike/password/", data={
        "old_password": "bad password over here",
        "new_password": "12345678",
    })
    assert password.status_code == 400
    assert password.json()['old_password'][0] == "Wrong Password"

    # change the password properly
    password = client.post("/api/users/mike/password/", data={
        "old_password": "mike",
        "new_password": "12345678",
    })
    assert password.status_code == 200

    # check new login
    client.logout()
    assert client.login(username='mike', password='12345678')

    # check that mike can't change joe's password
    password = client.post("/api/users/joe/password/", data={
        "old_password": "joe",
        "new_password": "12345678",
    })
    assert password.status_code == 403
    assert password.json() == {
        'detail': "Only admins can change other user's passwords"
    }

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
    assert get_mike.json()['is_active'] == True

    # set mike as inactive
    set_inactive_mike = client.put('/api/users/mike/active/', data={
        'is_active': False
    })
    assert set_inactive_mike.status_code == 200
    get_mike = client.get('/api/users/mike/')
    assert get_mike.status_code == 200
    assert get_mike.json()['is_active'] == False

    # set mike as active again
    set_active_mike = client.put('/api/users/mike/active/', data={
        'is_active': True
    })
    assert set_active_mike.status_code == 200
    get_mike = client.get('/api/users/mike/')
    assert get_mike.status_code == 200
    assert get_mike.json()['is_active'] == True

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

def test_whoami(client, admin_user):
    whoami = client.get('/api/users/whoami/')
    assert whoami.status_code == 200
    assert whoami.json() == {'is_authenticated': False}

    assert client.login(username='admin', password='q')
    whoami = client.get('/api/users/whoami/')
    assert whoami.status_code == 200
    assert whoami.json()['is_authenticated'] == True
    assert whoami.json()['username'] == 'admin'
    assert whoami.json()['is_admin'] == True

    client.logout()
    whoami = client.get('/api/users/whoami/')
    assert whoami.status_code == 200
    assert whoami.json() == {'is_authenticated': False}

def test_username_validation(client, admin_user):
    GOOD_USERNAMES = [
        'alpha0123',
        'phillip.glass',
        'erik_satie',
        'yet_another.badly.named_user',
        'johnDoe',
    ]
    BAD_USERNAMES = [
        'beta!',
        'this-username-is-no-good',
        'sh',  # length 2 < 3
        'x',
        'long username' * 5,  # length 65 > 64
        'money&power',
    ]
    USER_STUB = {
        "is_admin": False,
        "first_name": "first name",
        "last_name": "last name",
        "is_active": True,
    }

    assert client.login(username='admin', password='q')

    for username in GOOD_USERNAMES:
        data = USER_STUB.copy()
        data['username'] = username
        post = client.post('/api/users/', data=data)
        assert post.status_code == 201

    for username in BAD_USERNAMES:
        data = USER_STUB.copy()
        data['username'] = username
        post = client.post('/api/users/', data=data, format='json')
        assert post.status_code == 400
