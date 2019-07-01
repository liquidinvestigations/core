from django.apps import AppConfig


class HomeConfig(AppConfig):
    name = 'liquidcore.home'

    def ready(self):
        from . import signals  # noqa: F401
