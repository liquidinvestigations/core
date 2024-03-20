import logging

from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import oauth2_provider.models
from django.contrib.auth.admin import User
import requests

from .health_checks import get_report as get_health_check_report

log = logging.getLogger(__name__)


@login_required
def homepage(request):
    return render(request, 'homepage.html', {
        'liquid_title': settings.LIQUID_TITLE,
        'liquid_apps': settings.LIQUID_APPS,
        'liquid_version': settings.LIQUID_VERSION,
        'liquid_core_version': settings.LIQUID_CORE_VERSION,
        'liquid_enable_dashboards': settings.LIQUID_ENABLE_DASHBOARDS,
        '2fa_enabled': settings.LIQUID_2FA,
        'health_report': get_health_check_report(),
    })


@login_required
def healthchecks_page(request):
    return render(request, 'healthcheck.html', {
        'health_report': get_health_check_report(),
        'liquid_version': settings.LIQUID_VERSION,
        'liquid_title': settings.LIQUID_TITLE,
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
        token = request.GET.get('access_token', '')
        if token:
            user_id = oauth2_provider.models.AccessToken.objects.get(token=token).user_id
            user = User.objects.get(id=user_id)

    if not user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    fake_user_email = user.get_username() + '@' + settings.LIQUID_DOMAIN
    user_app_perms = app_permissions(user)

    # Guests needed to map wikijs groups
    roles = ['user', 'Guests']
    if user.is_staff:
        roles.append('admin')
    if user.is_superuser:
        roles.append('superuser')
        # needed to map wikijs groups
        roles.append('Administrators')

    return JsonResponse({
        'id': user.get_username(),
        'login': user.get_username(),
        # WARNING: DO NOT USE user.email as that is overridden by the admin.
        # This causes problems in apps, e.g. the email is duplicated by the
        # admin, or some apps have bugs (.e.g Wiki.js)
        'email': fake_user_email,
        'is_admin': user.is_staff,
        'name': user.get_full_name() or user.get_username(),
        # These roles are used by the ouauth2proxy to restrict app access.
        # The proxy expects the group to
        # match the app id from the configuration.
        'roles': roles + user_app_perms,
        # OpenID (matrix)
        "sub": fake_user_email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "__str__": str(user),
        "__type__": str(type(user)),
    })


@csrf_exempt
@login_required
def proxy_dashboards(request):
    assert settings.LIQUID_ENABLE_DASHBOARDS
    assert request.user.is_superuser and request.user.is_staff

    url = None
    headers = dict(request.headers)
    for prefix in [
                    '/snoop', '/grafana', '/_search_rabbit',
                    '/_snoop_rabbit', '/_snoop_pgwatch2',
                ]:
        if request.path.startswith(prefix):
            url = settings.LIQUID_DASHBOARDS_PROXY_BASE_URL \
                + request.get_full_path()
            # tried to add `guest / guest` login for rabbitmq,
            # but queue urls don't work with this
            # if '_rabbit' in prefix:
            #     headers['Authorization'] ='Basic Z3Vlc3Q6Z3Vlc3Q='
            break
    if not url:
        for nomad_prefix in ['/ui', '/v1']:
            if request.path.startswith(nomad_prefix):
                url = settings.LIQUID_DASHBOARDS_PROXY_NOMAD_URL \
                    + request.get_full_path()
                break
    # Consul does not work; maybe if we check referer headers.
    if not url:
        if request.path.startswith('/consul_ui'):
            url = settings.LIQUID_DASHBOARDS_PROXY_CONSUL_URL \
                + request.get_full_path()
    assert url is not None

    try:
        response = requests.Session().send(
                requests.Request(request.method, url,
                                 headers=headers,
                                 data=request.body).prepare(),
                stream=True,
                timeout=600,
        )

        chunk_size = 1024
        if response.headers.get('transfer-encoding') == 'chunked':
            chunk_size = 10
        streaming_resp = StreamingHttpResponse(
            response.iter_content(chunk_size=chunk_size),
            content_type=response.headers.get('content-type'),
            status=response.status_code,
            reason=response.reason)
        return streaming_resp
    except Exception as e:
        log.exception(e)
        raise
