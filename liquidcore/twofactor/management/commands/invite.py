from django.conf import settings
from django.core.management.base import BaseCommand
from ... import invitations


class Command(BaseCommand):

    help = "Create invitation for user to set up TOTP"

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--duration', type=int,
                            default=settings.LIQUID_2FA_INVITATION_VALID,
                            help="Invitation valid time (minutes)")
        parser.add_argument('--create', action='store_true')

    def handle(self, username, duration, create, **options):
        print('inviting', 'new user' if create else 'existing user', username)
        url = invitations.invite(username, duration=duration, create=create)
        print(url)
