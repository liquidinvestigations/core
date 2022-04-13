import pytest
from liquidcore.twofactor import devices
from django_otp.oath import hotp
from collections import namedtuple

NORMAL_USER_NAME = 'user'
NORMAL_USER_PW = 'password'
ADMIN_NAME = 'admin'
ADMIN_PW = 'admin-password'
ADMIN_EMAIL = 'test@admin.com'


def _totp(device, now):
    counter = int(now.timestamp() - device.t0) // device.step
    return hotp(device.bin_key, counter)


def is_logged_in(client):
    resp = client.get('/', follow=False)
    return resp.status_code == 200


def _reset_last_use(device):
    device.refresh_from_db()
    device.last_t = -1
    device.save()


def payload(username, password, otp_token=None):
    if otp_token:
        return {'username': username,
                'password': password,
                'otp_token': otp_token}

    else:
        return {'username': username, 'password': password}


@pytest.fixture
def create_user(django_user_model):
    # The password cannot be retrieved from the user directly so a tuple needs
    # to be returned
    User = namedtuple('User', ['user', 'password'])
    return User(user=(django_user_model.objects
                      .create_user(username=NORMAL_USER_NAME,
                                   password=NORMAL_USER_PW)),
                password=NORMAL_USER_PW)


@pytest.fixture
def create_admin(django_user_model):
    # The password cannot be retrieved from the user directly so a tuple needs
    # to be returned
    Admin = namedtuple('Admin', ['admin', 'password'])
    return Admin(admin=(django_user_model.objects
                        .create_superuser(
                            username=ADMIN_NAME,
                            email=ADMIN_EMAIL,
                            password=ADMIN_PW
                            )),
                 password=ADMIN_PW)


@pytest.fixture
def create_device():
    def create_device(**kwargs):
        device = devices.create(**kwargs)
        device.confirmed = True
        device.save()
        _reset_last_use(device)
        return device
    return create_device


@pytest.fixture
def use_liquid_apps(settings):
    settings.LIQUID_APPS = [
        {
            'id': 'rocketchat',
            'enabled': True,
            'url': 'liquid.test.rocketchat',
        },
        {
            'id': 'hoover',
            'enabled': True,
            'url': 'liquid.test.hoover'
        },
        {
            'id': 'dokuwiki',
            'enabled': True,
            'url': 'liquid.test.dokuwiki',
        },
    ]
