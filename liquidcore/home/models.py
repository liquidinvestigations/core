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
        ]


# we need to override the __str__ method to only display the name
# instead of contenttype | name in the admin panel
Permission.__str__ = lambda self: f'{self.name}'
