from django.urls import reverse


def test_profile(client, create_user):
    url = reverse('profile')
    resp = client.get(url)
    assert resp.status_code == 401
    client.login(username=create_user.user.get_username(),
                 password=create_user.password)
    resp = client.get(url)
    assert resp.status_code == 200
