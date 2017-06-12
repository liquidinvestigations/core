from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.conf import settings

from . import discovery

def homepage(request):
    return render(request, 'homepage.html', {
        'hypothesis_app_url': settings.HYPOTHESIS_APP_URL,
        'hoover_app_url': settings.HOOVER_APP_URL,
        'node_hostnames': [node['hostname'] for node in discovery.nodes.values()],
    })

def profile(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponse('Unauthorized', status=401)
    return JsonResponse({
        'login': user.get_username(),
        'email': user.email,
    })

def nodes(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponse('Unauthorized', status=401)
    return JsonResponse(discovery.nodes)
