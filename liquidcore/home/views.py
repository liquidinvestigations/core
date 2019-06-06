from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.conf import settings


def homepage(request):
    return render(request, 'homepage.html', {
        'hypothesis_app_url': settings.HYPOTHESIS_APP_URL,
        'hoover_app_url': settings.HOOVER_APP_URL,
        'dokuwiki_app_url': settings.DOKUWIKI_APP_URL,
        'rocketchat_app_url': settings.ROCKETCHAT_APP_URL,
        'nextcloud_app_url': settings.NEXTCLOUD_APP_URL,
    })


def profile(request):
    user = request.user

    if not user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    return JsonResponse({
        'id': user.get_username(),
        'login': user.get_username(),
        'email': user.email,
        'is_admin': user.is_staff,
    })
