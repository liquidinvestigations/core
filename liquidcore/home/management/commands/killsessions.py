from django.core.management.base import BaseCommand
from ...auth import kill_sessions


class Command(BaseCommand):

    help = "Log out all users"

    def handle(self, **options):
        kill_sessions()
