import pytest
from liquidcore.twofactor import devices
from django_otp.oath import hotp

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


@pytest.fixture
def create_user(django_user_model):
    return {
            'user': (django_user_model.objects
                     .create_user(username=NORMAL_USER_NAME,
                                  password=NORMAL_USER_PW)),
            'password': NORMAL_USER_PW,
    }


@pytest.fixture
def create_admin(django_user_model):
    return {
        'admin': (django_user_model.objects
            .create_superuser(
                username='testadmin',
                email='test@mail.com',
                password='admin-pw'
                )),
        'password': ADMIN_PW,
    }


@pytest.fixture
def create_device():
    def create_device(**kwargs):
        device = devices.create(**kwargs)
        device.confirmed = True
        device.save()
        _reset_last_use(device)
        return device
    return create_device

