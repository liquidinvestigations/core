from django.utils.timezone import now
from time import sleep
from conftest import _totp, _reset_last_use, payload
from django.urls import reverse


ADMIN_URL = '/admin/'


def get_login_url():
    return reverse('login')


def test_admin_login_totp(client, create_admin, create_device):
    device = create_device(user=create_admin.admin)
    client.post(get_login_url(), payload('badusername',
                                         create_admin.password,
                                         _totp(device, now())))
    response = client.get(ADMIN_URL)
    assert response.status_code == 302
    assert response.url == '/admin/login/?next=/admin/'

    sleep(30)
    _reset_last_use(device)
    client.post(get_login_url(), payload(create_admin.admin.get_username(),
                                         'baddpassword',
                                         _totp(device, now())))
    response = client.get(ADMIN_URL)
    assert response.status_code == 302
    assert response.url == '/admin/login/?next=/admin/'

    sleep(30)
    _reset_last_use(device)
    client.post(get_login_url(), payload(create_admin.admin.get_username(),
                                         create_admin.password,
                                         999999))
    response = client.get(ADMIN_URL)
    assert response.status_code == 302
    assert response.url == '/admin/login/?next=/admin/'

    sleep(30)
    _reset_last_use(device)
    client.post(get_login_url(), payload(create_admin.admin.get_username(),
                                         create_admin.password,
                                         _totp(device, now())))
    _reset_last_use(device)
    client.post(get_login_url(), {
        'username': create_admin.admin.get_username(),
        'password': create_admin.password,
        'otp_token': _totp(device, now())
    })
    response = client.get(ADMIN_URL)
    assert response.template_name == 'admin/index.html'


def test_admin_standard_user(client, create_user):
    client.login(username=create_user.user.get_username(),
                 password=create_user.password)
    response = client.get(ADMIN_URL)
    # django will redirect to admin login page, so 302 is expected
    assert response.status_code == 302
    assert response.url == '/admin/login/?next=/admin/'
