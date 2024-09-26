from django.core.management.base import BaseCommand
from ...demo import create_demo_user


class Command(BaseCommand):
    help = "Add demo user."

    def handle(self, *args, **options):
        create_demo_user()
        print('Created demo user!')
