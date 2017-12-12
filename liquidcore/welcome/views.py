from pathlib import Path
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from ..config.models import Setting
from ..config.system import reconfigure_system

WELCOME_DONE = Path('/var/lib/liquid/core/welcome_done')


def should_welcome():
    return not WELCOME_DONE.is_file()


def welcome(request):
    if not should_welcome():
        return HttpResponseRedirect('/')

    if request.method == 'POST':
        domain = Setting.objects.get(name='domain')
        domain.data = request.POST['domain']
        domain.save()

        User.objects.create_user(
            username=request.POST['admin-username'],
            password=request.POST['admin-password'],
            is_staff=True,
            is_superuser=True
        )

        reconfigure_system()

        WELCOME_DONE.touch()

        return render(request, 'welcome-applying.html', {
            'url': 'http://' + request.POST['domain'],
        })

    return render(request, 'welcome.html')
