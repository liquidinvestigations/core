from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

import requests


@login_required
def homepage(request):
    return render(request, 'homepage.html', {
        'liquid_title': settings.LIQUID_TITLE,
        'liquid_apps': settings.LIQUID_APPS,
        'liquid_version': settings.LIQUID_VERSION,
        'liquid_core_version': settings.LIQUID_CORE_VERSION,
        '2fa_enabled': settings.LIQUID_2FA,
    })


def app_permissions(user):
    '''Helper function to create a list with names
    of the allowed apps for a user.'''
    app_perms = []
    for liquid_app in settings.LIQUID_APPS:
        id = liquid_app['id']
        if user.has_perm((f'home.use_{id}')):
            app_perms.append(id)
    return app_perms


def profile(request):
    user = request.user

    if not user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    user_email = user.get_username() + '@' + settings.LIQUID_DOMAIN
    user_app_perms = app_permissions(user)

    roles = ['user']
    if user.is_staff:
        roles.append('admin')
    if user.is_superuser:
        roles.append('superuser')

    return JsonResponse({
        'id': user.get_username(),
        'login': user.get_username(),
        'email': user.email or user_email,
        'is_admin': user.is_staff,
        'name': user.get_full_name() or user.get_username(),
        # These roles are used by the ouauth2proxy to restrict app access.
        # The proxy expects the group to
        # match the app id from the configuration.
        'roles': roles + user_app_perms,
    })


@csrf_exempt
@login_required
def proxy_dashboards(request):
    assert settings.LIQUID_ENABLE_DASHBOARDS
    user = request.user
    assert user.is_superuser and user.is_staff

    url = None
    headers = dict(request.headers)
    for prefix in ['/snoop', '/grafana', '/_search_rabbit', '/_snoop_rabbit']:
        if request.path.startswith(prefix):
            url = settings.LIQUID_DASHBOARDS_PROXY_BASE_URL \
                + request.get_full_path()
            break
    if not url:
        for nomad_prefix in ['/ui', '/v1']:
            if request.path.startswith(nomad_prefix):
                url = settings.LIQUID_DASHBOARDS_PROXY_NOMAD_URL \
                    + request.get_full_path()
                # headers['Transfer-Encoding'] = 'chunked'
                break
    assert url is not None

    response = requests.get(url, stream=True, headers=headers)
    streaming_resp = StreamingHttpResponse(
        response.raw,
        content_type=response.headers.get('content-type'),
        status=response.status_code,
        reason=response.reason)
    for key, value in response.headers.items():
        streaming_resp[key] = value
    return streaming_resp
