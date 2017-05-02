from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = 'server.common'

    def ready(self):
        from . import signals
