import random
import math
from django.conf import settings
from django.db import models
from django.utils.timezone import now
from django_otp.plugins.otp_totp.models import TOTPDevice

VOCABULARY = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
REQUIRED_ENTROPY = 256


def random_code():
    entropy_per_char = math.log(len(VOCABULARY), 2)
    chars = int(math.ceil(REQUIRED_ENTROPY / entropy_per_char))
    urandom = random.SystemRandom()
    return ''.join(urandom.choice(VOCABULARY) for _ in range(chars))


class TOTPDeviceTimed(TOTPDevice):
    created = models.DateTimeField(auto_now_add=True)


class Invitation(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    code = models.CharField(max_length=200, default=random_code)
    expires = models.DateTimeField()
    opened_at = models.DateTimeField(null=True)
    used = models.BooleanField(default=False)
    device = models.OneToOneField(TOTPDeviceTimed,
                                  null=True,
                                  on_delete=models.SET_NULL)

    @property
    def state(self):
        if self.used:
            return 'used'
        if self.opened_at:
            return 'opened'
        if now() > self.expires:
            return 'expired'
        return 'valid'
