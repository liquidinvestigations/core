from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required


@login_required
def homepage(request):
    return render(request, 'homepage.html', {
        'liquid_title': settings.LIQUID_TITLE,
        'hypothesis_app_url': settings.HYPOTHESIS_APP_URL,
        'hoover_app_url': settings.HOOVER_APP_URL,
        'dokuwiki_app_url': settings.DOKUWIKI_APP_URL,
        'rocketchat_app_url': settings.ROCKETCHAT_APP_URL,
        'nextcloud_app_url': settings.NEXTCLOUD_APP_URL,
        'codimd_app_url': settings.CODIMD_APP_URL,
    })


def profile(request):
    user = request.user

    if not user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    user_email = user.get_username() + '@' + settings.LIQUID_DOMAIN

    return JsonResponse({
        'id': user.get_username(),
        'login': user.get_username(),
        'email': user.email or user_email,
        'is_admin': user.is_staff,
        'name': user.get_full_name() or user.get_username(),
        'roles': ['admin', 'user'] if user.is_staff else ['user'],
    })
