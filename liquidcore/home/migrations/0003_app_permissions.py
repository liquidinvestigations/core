from django.db import migrations
from django.contrib.auth.models import User, Permission
from django.conf import settings


class Migration(migrations.Migration):

    def add_user_permissions(apps, schema_editor):
        for x in Permission.objects.all():
            print(x)
        for user in User.objects.all():
            for liquid_app in settings.LIQUID_APPS:
                id = liquid_app['id']
                if liquid_app['adminOnly']:
                    continue
                permission = Permission.objects.get(codename=f'use_{id}')
                user.user_permissions.add(permission)
                user.save()

    dependencies = [
        ('home', '0003_auto_20220406_1047'),
    ]

    operations = [
        migrations.RunPython(add_user_permissions)
    ]
