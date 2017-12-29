import json
from pathlib import Path
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from ..config.models import Setting
from ..config.system import reconfigure_system

WELCOME_DONE = Path('/var/lib/liquid/core/welcome_done')
USERS_FILE = Path('/var/lib/liquid/core/users.json')


def should_welcome():
    return not WELCOME_DONE.is_file()


def welcome(request):
    if not should_welcome():
        return HttpResponseRedirect('/')

    if request.method == 'POST':
        domain = Setting.objects.get(name='domain')
        domain.data = request.POST['domain']
        domain.save()

        user_info = dict(
            username=request.POST['admin-username'],
            password=request.POST['admin-password'],
            is_admin=True,
        )
        with USERS_FILE.open('w') as f:
            json.dump(user_info, f)

        reconfigure_system()

        return render(request, 'welcome-applying.html', {
            'url': 'http://' + request.POST['domain'],
        })

    return render(request, 'welcome.html')
