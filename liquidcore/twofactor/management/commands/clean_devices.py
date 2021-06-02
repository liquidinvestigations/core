from django.core.management.base import BaseCommand
from django_otp.plugins.otp_totp.models import TOTPDevice


def remove_unconfirmed_devices():
    TOTPDevice.objects.all().filter(confirmed=False).delete()


class Command(BaseCommand):

    help = "Remove unconfirmed devices."

    def handle(self, *args, **options):
        remove_unconfirmed_devices()
