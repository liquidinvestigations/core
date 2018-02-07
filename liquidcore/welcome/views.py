import json
from pathlib import Path
from django.shortcuts import render
from django.http import HttpResponseRedirect
from ..config.models import Setting
from ..config.system import reconfigure_system
from django.http import JsonResponse

WELCOME_DONE = Path('/var/lib/liquid/core/welcome_done')
WELCOME_STARTED = Path('/var/lib/liquid/core/welcome_started')
USERS_FILE = Path('/var/lib/liquid/core/users.json')


def should_welcome():
    return not WELCOME_DONE.is_file()


def has_welcome_started():
    return WELCOME_STARTED.is_file()


def get_welcome_domain():
    with WELCOME_STARTED.open('r') as f:
        return f.read()


def welcome_done(request):
    data = {
        "done": not should_welcome(),
        "started": has_welcome_started(),
    }
    if data['started']:
        data['domain'] = get_welcome_domain()

    return JsonResponse(data)


def welcome(request):
    if not should_welcome():
        return HttpResponseRedirect('/')

    if request.method == 'POST':
        domain_value = request.POST['domain']

        domain = Setting.objects.get(name='domain')
        domain.data = domain_value
        domain.save()

        vpn_setting = Setting.objects.get(name='vpn')
        vpn = vpn_setting.data
        vpn['server']['address']['address'] = domain_value
        vpn_setting.data = vpn
        vpn_setting.save()

        user_info = dict(
            username=request.POST['admin-username'],
            password=request.POST['admin-password'],
            is_admin=True,
        )
        with USERS_FILE.open('w') as f:
            json.dump([user_info], f)

        reconfigure_system()

        with WELCOME_STARTED.open('w') as f:
            f.write(domain_value)

        return HttpResponseRedirect('/welcome/')

    elif request.method == 'GET':
        if has_welcome_started():
            return render(request, 'welcome-applying.html', {
                'url': 'http://' + get_welcome_domain(),
            })
        else:
            return render(request, 'welcome.html')
