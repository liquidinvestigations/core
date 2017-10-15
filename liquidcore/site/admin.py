from django.conf.urls import url
from django.contrib.admin import AdminSite, site as default_site
from ..config import system


class LiquidAdminSite(AdminSite):

    site_header = 'Liquid Node administration'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registry.update(default_site._registry)

    def get_urls(self):
        return super().get_urls() + [
            url(r'config/$', system.admin),
            url(r'config/(?P<job_id>[^/]+)\.log$', system.admin_log),
        ]


admin_site = LiquidAdminSite()
