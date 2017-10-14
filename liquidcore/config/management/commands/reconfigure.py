from django.core.management.base import BaseCommand
from ... import reconfigure


class Command(BaseCommand):

    help = "Reconfigure the system"

    def handle(self, **options):
        reconfigure.reconfigure_system()
