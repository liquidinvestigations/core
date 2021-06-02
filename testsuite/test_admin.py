from django.utils.timezone import now
from conftest import _totp, is_logged_in


URL = '/admin/'


def test_admin_page_login_totp(client, create_admin, create_device):
    device = create_device(user=create_admin.admin)
    response = client.post(URL, {
        'username': create_admin.admin.get_username(),
        'password': create_admin.password,
        'otp_token': _totp(device, now())
    }, follow=True)
    # import pdb; pdb.set_trace()
    assert response.status_code == 200


def test_admin_standard_user(client, create_user):
    client.login(username=create_user.user.get_username(),
                 password=create_user.password)
    response = client.get(URL)
    import pdb; pdb.set_trace()
    # django will redirect to admin login page, so 302 is expected
    assert response.status_code == 302
    assert response.url == '/admin/login/?next=/admin/'
