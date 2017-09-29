import json
from django.conf import settings
from django.db import models

class Service(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    is_enabled = models.BooleanField()
    state = models.CharField(max_length=30, blank=True)
    state_description = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    @property
    def url(self):
        return self.name + "." + settings.LIQUID_DOMAIN


class Setting(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    data_text = models.TextField()

    @property
    def data(self):
        return json.loads(self.data_text)

    @data.setter
    def data(self, data):
        self.data_text = json.dumps(data)


class Node(models.Model):
    name = models.CharField(max_length=255)
    trusted = models.BooleanField(default=False)
    address = models.CharField(max_length=50)
    data_text = models.TextField()

    @property
    def data(self):
        return json.loads(self.data_text)

    @data.setter
    def data(self, data):
        self.data_text = json.dumps(data)
