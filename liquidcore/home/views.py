from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required


@login_required
def homepage(request):
    return render(request, 'homepage.html', {
        'liquid_title': settings.LIQUID_TITLE,
        'liquid_apps': settings.LIQUID_APPS,
        'liquid_version': settings.LIQUID_VERSION,
        'liquid_core_version': settings.LIQUID_CORE_VERSION,
        '2fa_enabled': settings.LIQUID_2FA,
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
