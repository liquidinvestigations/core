import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):

    help = "Create users according to json file"

    def add_arguments(self, parser):
        parser.add_argument('users_file')

    def handle(self, users_file, **options):
        with open(users_file, encoding='utf8') as f:
            users = json.load(f)

        for data in users:
            user = User.objects.filter(username=data['username']).first()
            if user is None:
                print("Creating user", data['username'])
                user = User.objects.create_user(
                    username=data['username'],
                    password=data['password'],
                )

            else:
                print("Updating user", data['username'])
                user.set_password(data['password'])

            is_admin = bool(data.get('is_admin'))
            user.is_superuser = is_admin
            user.is_staff = is_admin
            user.save()
