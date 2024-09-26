from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
import os


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # before view is called
        if os.path.exists(settings.MAINTENANCE_FILE):
            context = {
                'last_reset': last_reset(),
            }
            return render(request, 'maintenance.html', context)
        response = self.get_response(request)

        return response


def last_reset():
    now = timezone.now()
    last_hour = now.replace(minute=0, second=0, microsecond=0)
    timezone_name = last_hour.tzname()
    return f'{last_hour}  {timezone_name}'
