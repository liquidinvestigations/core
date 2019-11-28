from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):

    help = "Grant admin privileges to this user"

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, username, **options):
        user = User.objects.get(username=username)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f"{user} is now admin")
