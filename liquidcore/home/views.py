from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.utils.dateparse import parse_datetime

from . import discover

def homepage(request):
    status = discover.get_status().get("status")
    nodes = discover.get_node_list() if status else {}
    for interface in nodes:
        for name in nodes[interface]:
            nodes[interface][name]['discovered_at_datetime'] = \
                    parse_datetime(nodes[interface][name]['discovered_at'])

    return render(request, 'homepage.html', {
        'status': status,
        'nodes': nodes,
        'hypothesis_app_url': settings.HYPOTHESIS_APP_URL,
        'hoover_app_url': settings.HOOVER_APP_URL,
        'dokuwiki_app_url': settings.DOKUWIKI_APP_URL,
    })

def profile(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponse('Unauthorized', status=401)
    return JsonResponse({
        'login': user.get_username(),
        'email': user.email,
    })
