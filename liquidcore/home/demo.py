from django.conf import settings
from django.contrib.auth.admin import User
from django.contrib.auth.models import Permission


class DemoModeAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # before view is called
        if settings.DEMO_MODE_ENABLED:
            print('demo mode request')
            try:
                demo_user = User.objects.get(username='demo')
            except User.DoesNotExist:
                demo_user = create_demo_user()
            request.user = demo_user

        response = self.get_response(request)

        return response


def create_demo_user():
    demo_username = 'demo'
    demo_user, _ = User.objects.get_or_create(username=demo_username)
    hoover_perm = Permission.objects.get(codename='use_hoover')
    nextcloud_perm = Permission.objects.get(codename='use_nextcloud28')
    demo_user.user_permissions.add(hoover_perm)
    demo_user.user_permissions.add(nextcloud_perm)
    demo_user.save()
    return demo_user
