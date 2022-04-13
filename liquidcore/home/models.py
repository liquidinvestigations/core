from django.db import models


class AppPermissions(models.Model):
    '''Model to add permissions for using liquid apps.'''
    class Meta:
        permissions = [
            ('use_nextcloud', 'Can use Nextcloud'),
            ('use_codimd', 'Can use CodiMD'),
            ('use_dokuwiki', 'Can use dokuwiki'),
            ('use_hoover', 'Can use hoover'),
            ('use_rocketchat', 'Can use rocketchat'),
            ('use_hypothesis', 'Can use hypothesis'),
        ]
