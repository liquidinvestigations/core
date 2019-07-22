from django.conf import settings
from django.contrib.auth.backends import ModelBackend

staff_only = settings.AUTH_STAFF_ONLY


class AuthBackend(ModelBackend):

    def user_can_authenticate(self, user):
        if staff_only and not user.is_staff:
            return False

        return super().user_can_authenticate(user)
