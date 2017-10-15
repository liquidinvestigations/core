import json
from django.core.management.base import BaseCommand
from ... import system


class Command(BaseCommand):

    help = "Inspect the system configuration"

    def add_arguments(self, parser):
        parser.add_argument('key', default=None)

    def handle(self, key, **options):
        value = system.get_config(key)
        print(json.dumps(value, indent=2, sort_keys=True))
