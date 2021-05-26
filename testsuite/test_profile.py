def test_profile(client, test_user, test_user_name, test_user_pw):
    resp = client.get('/accounts/profile')
    assert resp.status_code == 401
    test_user()
    client.login(username=test_user_name, password=test_user_pw)
    resp = client.get('/accounts/profile')
    assert resp.status_code == 200
