def test_profile(client, test_user):
    resp = client.get('/accounts/profile')
    assert resp.status_code == 401
    user = test_user()
    client.login(username=user['username'], password=user['password'])
    resp = client.get('/accounts/profile')
    assert resp.status_code == 200
