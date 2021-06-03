from django.core.management.base import BaseCommand
from liquidcore.twofactor.models import TOTPDeviceTimed
from datetime import timedelta
from django.utils import timezone


def remove_unconfirmed_devices():
    TOTPDeviceTimed.objects.all() \
                   .filter(confirmed=False,
                           created__lte=timezone.now()
                           - timedelta(minutes=1)) \
                   .select_related('totpdevice_ptr') \
                   .delete()


class Command(BaseCommand):

    help = "Remove unconfirmed devices."

    def handle(self, *args, **options):
        remove_unconfirmed_devices()
