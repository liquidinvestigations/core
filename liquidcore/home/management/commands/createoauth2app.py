import json
from django.core.management.base import BaseCommand
from oauth2_provider.models import Application


class Command(BaseCommand):

    help = "Create an OAuth2 app and print client_id and client_secret as json"

    def add_arguments(self, parser):
        parser.add_argument('app_name')
        parser.add_argument('redirect_uri')
        parser.add_argument('--algo')
        parser.add_argument('--noskip')

    def handle(self, app_name, redirect_uri, **options):
        app, _ = Application.objects.get_or_create(name=app_name)
        app.redirect_uris = redirect_uri
        app.client_type = 'confidential'
        app.authorization_grant_type = 'authorization-code'
        app.user_id = None

        if options['noskip']:
            app.skip_authorization = False
        else:
            app.skip_authorization = True

        if options['algo']:
            app.algorithm = options['algo']

        app.save()

        keys = {
            'client_id': app.client_id,
            'client_secret': app.client_secret,
        }
        print(json.dumps(keys))
