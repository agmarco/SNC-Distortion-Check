from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class EmailAuthConfig(AppConfig):
    name = 'server.emailauth'
    verbose_name = _("Email Authentication")
