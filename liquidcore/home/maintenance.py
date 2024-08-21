from django.http import HttpResponse
from django.conf import settings
import os


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # before view is called
        if os.path.exists(settings.MAINTENANCE_FILE):
            return HttpResponse(
                open(settings.MAINTENANCE_HTML).read(), content_type='text/html'
            )

        response = self.get_response(request)

        return response
