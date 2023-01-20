import random
import math
from django.conf import settings
from django.db import models
from django_otp.plugins.otp_totp.models import TOTPDevice

VOCABULARY = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
REQUIRED_ENTROPY = 256


def random_code():
    entropy_per_char = math.log(len(VOCABULARY), 2)
    chars = int(math.ceil(REQUIRED_ENTROPY / entropy_per_char))
    urandom = random.SystemRandom()
    return ''.join(urandom.choice(VOCABULARY) for _ in range(chars))


class Invitation(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    code = models.CharField(max_length=200, default=random_code)
    expires = models.DateTimeField()
    STATE_CHOICES = [
        ('valid', 'valid'),
        ('used', 'used'),
        ('expired', 'expired'),
    ]
    state = models.CharField(max_length=200, choices=STATE_CHOICES, default='valid')


class TOTPDeviceTimed(TOTPDevice):
    created = models.DateTimeField(auto_now_add=True)
