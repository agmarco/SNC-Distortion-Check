import os
import json
import requests
from django.utils.safestring import mark_safe
from requests.exceptions import ConnectionError

from django import template
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static

register = template.Library()


@register.simple_tag
def webpack(path):
    """Use the webpack dev server in development, and staticfiles in production."""

    if not settings.DEBUG:

        # load the correct file from the manifest.json
        dirname, basename = os.path.split(path)
        with open(os.path.join(settings.BASE_DIR, 'client/dist', dirname, 'manifest.json')) as manifest_file:
            manifest = json.load(manifest_file)
            filename = manifest[basename]
        return static(os.path.join(dirname, filename))

    else:
        webpack_path = os.path.join('http://0.0.0.0:8080/', path)

        try:
            res = requests.get(webpack_path)
        except ConnectionError:
            return static(path)

        if res.status_code == 200:
            return webpack_path
        else:
            return static(path)


@register.simple_tag
def manifest(dirname):
    """Add the webpack chunk manifest to the global scope."""

    with open(os.path.join(settings.BASE_DIR, 'client/dist', dirname, 'chunk-manifest.json')) as manifest_file:
        manifest = json.load(manifest_file)

    return mark_safe(f"""
    //<![CDATA[
        window.webpackManifest = {json.dumps(manifest)};
    //]]>
    """) if not settings.DEBUG else ''
