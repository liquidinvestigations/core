from django.core.management.base import BaseCommand
from ... import system


class Command(BaseCommand):

    help = "Reconfigure the system"

    def handle(self, **options):
        system.update_system()
