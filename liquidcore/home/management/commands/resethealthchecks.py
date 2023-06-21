from django.core.management.base import BaseCommand
from ...health_checks import reset


class Command(BaseCommand):
    help = "Reset health checks when restarting container"

    def handle(self, **options):
        reset()
