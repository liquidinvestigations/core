from django.core.management.base import BaseCommand
from ...health_checks import update


class Command(BaseCommand):
    help = "Update health checks by querying consul"

    def handle(self, **options):
        update()
