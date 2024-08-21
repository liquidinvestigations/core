from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    help = "Turn maintenance mode on and off."

    def add_arguments(self, parser):
        parser.add_argument(
            '--on',
            action='store_true',
        )
        parser.add_argument(
            '--off',
            action='store_true',
        )

    def handle(self, *args, **options):
        maintenance_file = '/app/maintenance'
        if options['on']:
            with open(maintenance_file, 'w'):
                pass
        elif options['off']:
            if os.path.exists(maintenance_file):
                os.remove(maintenance_file)
