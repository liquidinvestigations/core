from django.core.management.base import BaseCommand
from ...health_checks import print_report


class Command(BaseCommand):
    help = "Print health checks page info"

    def handle(self, **options):
        print_report()
