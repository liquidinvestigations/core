# Generated by Django 3.1.3 on 2023-03-02 21:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_auto_20230302_2001'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='apppermissions',
            options={'permissions': [('use_nextcloud', 'Can use Nextcloud'), ('use_nextcloud-instance-2', 'Can use Nextcloud Instance 2'), ('use_codimd', 'Can use CodiMD'), ('use_dokuwiki', 'Can use dokuwiki'), ('use_hoover', 'Can use hoover'), ('use_rocketchat', 'Can use rocketchat'), ('use_hypothesis', 'Can use hypothesis')]},
        ),
    ]
