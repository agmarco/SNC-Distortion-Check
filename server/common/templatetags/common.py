import os
import requests

from django import template
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static

register = template.Library()


@register.simple_tag
def webpack(path):
    """Use the webpack dev server in development, and staticfiles in production."""

    if not settings.DEBUG:
        return static(path)
    else:
        webpack_path = os.path.join('http://0.0.0.0:8080/', path)
        if requests.head(webpack_path).status_code == 200:
            return webpack_path
        else:
            return static(path)
