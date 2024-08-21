from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):

    help = "Check when the deme user was active the last time."

    def handle(self, *args, **kwargs):
        user = User.objects.get(username='demo')
        print(user.last_login)
