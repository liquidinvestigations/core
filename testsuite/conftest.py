import pytest
from liquidcore.twofactor import devices


@pytest.fixture
def test_user(django_user_model, test_user_name, test_user_pw):
    def make_user():
        return django_user_model.objects.create_user(username=test_user_name,
                                                     password=test_user_pw)
    return make_user


@pytest.fixture
def test_user_name():
    return 'testuser'


@pytest.fixture
def test_user_pw():
    return 'pw'


@pytest.fixture
def test_admin(django_user_model):
    def make_admin():
        return (django_user_model.objects
                .create_superuser(
                    username='testadmin',
                    email='test@mail.com',
                    password='admin-pw'
                    ))
    return make_admin


@pytest.fixture
def test_device():
    def create_device(**kwargs):
        device = devices.create(**kwargs)
        device.confirmed = True
        device.save()
        return device
    return create_device
