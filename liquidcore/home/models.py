from django.db import models
from django.contrib.auth.models import Permission


class AppPermissions(models.Model):
    '''Model to add permissions for using liquid apps.'''
    class Meta:
        permissions = [
            ('use_nextcloud', 'Can use Nextcloud'),
            ('use_nextcloud-instance-2', 'Can use Nextcloud Instance 2'),
            ('use_codimd', 'Can use CodiMD'),
            ('use_dokuwiki', 'Can use dokuwiki'),
            ('use_hoover', 'Can use hoover'),
            ('use_rocketchat', 'Can use rocketchat'),
            ('use_hypothesis', 'Can use hypothesis'),
            ('use_wikijs', 'Can use Wiki.js'),
            ('use_nextcloud28', 'Can use Nextcloud 28'),
            ('use_grist', 'Can use Grist worksheets'),
            ('use_prophecies', 'Can use ICIJ Prophecies'),

        ]


# we need to override the __str__ method to only display the name
# instead of contenttype | name in the admin panel
Permission.__str__ = lambda self: f'{self.name}'


class HealthCheckPing(models.Model):
    """Stores all previous health check results."""

    date = models.DateTimeField(auto_now_add=True, db_index=True)
    result = models.JSONField()
