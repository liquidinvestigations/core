from django.conf.urls import url
from django.contrib.admin import AdminSite
from django.contrib.admin import ModelAdmin
from django.contrib.admin import site as default_site
from ..config import models as config_models
from ..config import admin as config_admin


class LiquidAdminSite(AdminSite):

    site_header = 'Liquid Node administration'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registry.update(default_site._registry)

    def get_urls(self):
        return super().get_urls() + [
            url(r'reconfigure/$', config_admin.reconfigure),
            url(r'reconfigure/(?P<job_id>[^/]+)\.log$',
                config_admin.reconfigure_job_log),
        ]


admin_site = LiquidAdminSite()
admin_site.register(config_models.Setting, ModelAdmin)
admin_site.register(config_models.Service, ModelAdmin)
admin_site.register(config_models.Node, ModelAdmin)
admin_site.register(config_models.VPNClientKey, ModelAdmin)
