import json
from django.conf import settings
from django.db import models

SERVICE_URLS = {
    'hoover': settings.HOOVER_APP_URL,
    'hypothesis': settings.HYPOTHESIS_APP_URL,
    'dokuwiki': settings.DOKUWIKI_APP_URL,
    'matrix': settings.MATRIX_APP_URL,
    'davros': settings.DAVROS_APP_URL,
}


class Service(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    is_enabled = models.BooleanField()
    state = models.CharField(max_length=30, blank=True)
    state_description = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    @property
    def url(self):
        return SERVICE_URLS.get(self.name)

    @property
    def data(self):
        return {
            'name': self.name,
            'is_enabled': self.is_enabled,
            'state': self.state,
            'state_description': self.state_description,
            'error_message': self.error_message,
        }

    def __str__(self):
        return "{!r} = {}".format(self.name, self.data)


class Setting(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    data_text = models.TextField()

    @property
    def data(self):
        return json.loads(self.data_text)

    @data.setter
    def data(self, data):
        self.data_text = json.dumps(data)

    def __str__(self):
        return "{!r} = {}".format(self.name, self.data)


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

    def __str__(self):
        return "{!r} = {}".format(self.name, self.data)
