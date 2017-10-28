# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-10-11 19:30
from __future__ import unicode_literals

import json
from django.db import migrations


def create_setting_instances(apps, schema_editor):
    Setting = apps.get_model("config", "Setting")
    defaults = {
        "initialized": False,
        "domain": "liquid.example.org",
        "lan": {
            "ip": "10.0.0.1",
            "netmask": "255.255.255.0",
            "dhcp_range": "10.0.0.100-255",
            "hotspot": {
                "ssid": "",
                "password": "",
            },
            "eth": False,
        },
        "wan": {
            "wifi": {
                "ssid": "",
                "password": "",
            },
        },
        "ssh": {
            "enabled": False,
            "authorized_keys": [],
            "port": 22,
        },
    }

    for name, data in defaults.items():
        Setting(name=name, data_text=json.dumps(data)).save()


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0003_node'),
    ]

    operations = [
        migrations.RunPython(create_setting_instances),
    ]
