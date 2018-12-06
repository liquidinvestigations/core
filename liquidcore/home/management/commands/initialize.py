import subprocess
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    help = "Initialize app data"

    def handle(self, **options):
        subprocess.check_call(['./manage.py', 'migrate'])
