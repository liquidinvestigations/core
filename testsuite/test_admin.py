from django.utils.timezone import now
from test_twofactor_invitation import _totp


def test_admin_view(client, test_admin, test_device):
    admin = test_admin()
    device = test_device(user=admin)
    response = client.post('/admin/', {
        'username': 'testadmin',
        'password': 'admin-pw',
        'otp_token': _totp(device, now())
    }, follow=True)
    assert response.status_code == 200


def test_admin_standard_user(client, django_user_model):
    username = 'user1'
    password = 'password'
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    response = client.get('/admin/')
    # django will redirect to admin login page, so 302 is expected
    assert response.status_code == 302
