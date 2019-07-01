import sys
from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate


class Command(BaseCommand):

    help = "Check if username and password are correct"

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('password')

    def handle(self, username, password, **options):
        user = authenticate(username=username, password=password)
        if user is None:
            sys.exit(1)
        else:
            sys.exit(0)
