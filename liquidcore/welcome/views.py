from django.shortcuts import render
from django.contrib.auth.models import User
from ..config.models import Setting
from ..config.system import reconfigure_system


def welcome(request):
    if request.method == 'POST':
        domain = Setting.objects.get(name='domain')
        domain.data = request.POST['domain']
        domain.save()

        lan = Setting.objects.get(name='lan')
        lan.data = dict(lan.data, hotspot={
            'ssid': request.POST['hotspot-ssid'],
            'password': request.POST['hotspot-password'],
        })
        lan.save()

        User.objects.create_user(
            username=request.POST['admin-username'],
            password=request.POST['admin-password'],
            is_staff=True,
            is_superuser=True
        )

        reconfigure_system()

        return render(request, 'welcome-applying.html', {
            'ssid': request.POST['hotspot-ssid'],
            'url': 'http://' + request.POST['domain'],
        })

    return render(request, 'welcome.html')
