# Generated by Django 3.1.3 on 2023-06-20 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_auto_20230308_1934'),
    ]

    operations = [
        migrations.CreateModel(
            name='HealthCheckPing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('result', models.JSONField()),
            ],
        ),
    ]
