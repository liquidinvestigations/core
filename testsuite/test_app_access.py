from django.contrib.auth.models import Permission
from django.urls import reverse
import json
import re

APPS = ['hoover', 'nexctloud', 'rocketchat', 'codimd', 'dokuwiki']


def test_default_permissions(client, create_user):
    user = create_user.user

    print(user.user_permissions.all())
    for app in APPS:
        if app == 'rocketchat':
            assert user.has_perm('home.use_rocketchat')
        else:
            assert not user.has_perm(f'home.use_{app}')


def test_profile_roles(client, create_user, use_liquid_apps):
    user = create_user.user
    url = reverse('profile')
    client.login(username=user.username,
                 password=create_user.password)
    resp = client.get(url)
    profile = json.loads(resp.content)
    for app in APPS:
        if app == 'rocketchat':
            assert 'rocketchat' in profile['allowed_apps']
        else:
            assert app not in profile['allowed_apps']

    permission = Permission.objects.get(codename='use_hoover')
    user.user_permissions.add(permission)
    user.save()
    # it's necessary to login again because of autologout
    client.login(username=user.username,
                 password=create_user.password)
    new_resp = client.get(url)
    new_profile = json.loads(new_resp.content)
    assert 'hoover' in new_profile['allowed_apps']
    assert 'rocketchat' in new_profile['allowed_apps']


def test_html(client, create_user, use_liquid_apps):
    user = create_user.user
    client.login(username=user.username,
                 password=create_user.password)
    html = client.get(reverse('home')).content
    assert find_enabled_link(str(html), 'liquid.test.rocketchat')
    assert not find_enabled_link(str(html), 'liquid.test.hoover')
    assert not find_enabled_link(str(html), 'liquid.test.dokuwiki')

    permission = Permission.objects.get(codename='use_hoover')
    user.user_permissions.add(permission)
    user.save()
    # it's necessary to login again because of autologout
    client.login(username=user.username,
                 password=create_user.password)
    new_html = client.get(reverse('home')).content
    assert find_enabled_link(str(new_html), 'liquid.test.rocketchat')
    assert find_enabled_link(str(new_html), 'liquid.test.hoover')
    assert not find_enabled_link(str(new_html), 'liquid.test.dokuwiki')


def find_enabled_link(html, app):
    link_match = re.search(f'{app}".*?>', html)
    return 'inactiveLink' not in link_match.group(0)
