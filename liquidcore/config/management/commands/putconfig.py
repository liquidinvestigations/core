import json
from django.core.management.base import BaseCommand
from ... import system


class Command(BaseCommand):

    help = "Change the system configuration"

    def add_arguments(self, parser):
        parser.add_argument('key')
        parser.add_argument('value')

    def handle(self, key, value, **options):
        job = system.put_config(key, json.loads(value))
        job.wait()
