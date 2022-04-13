from django.db import migrations
from django.contrib.auth.models import User, Permission
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from ..models import AppPermissions


class Migration(migrations.Migration):

    def add_user_permissions(apps, schema_editor):
        content_type = ContentType.objects.get_for_model(AppPermissions)
        for user in User.objects.all():
            for liquid_app in settings.LIQUID_APPS:
                id = liquid_app['id']
                if liquid_app['adminOnly']:
                    continue
                permission, _ = Permission.objects.get_or_create(
                    codename=f'use_{id}',
                    name=f'Can use {id}',
                    content_type=content_type
                )
                user.user_permissions.add(permission)
                user.save()

    dependencies = [
        ('home', '0002_apppermissions'),
    ]

    operations = [
        migrations.RunPython(add_user_permissions)
    ]
