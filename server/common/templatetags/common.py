import os

from django import template
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static

register = template.Library()


# TODO should use static in dev if the webpack dev server isn't running
@register.simple_tag
def webpack(path):
    """Use the webpack dev server in development, and staticfiles in production."""

    return os.path.join('http://0.0.0.0:8080/', path) if settings.DEBUG else static(path)
