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
def webpack(app, bundle):
    """Use the webpack dev server in development, and staticfiles in production."""

    if settings.DEBUG:
        webpack_path = os.path.join('http://0.0.0.0:8080/', app, f'{bundle}.js')
        static_path = static(os.path.join(app, f'{bundle}.js'))

        try:
            res = requests.get(webpack_path)
        except ConnectionError:
            return static_path

        if res.status_code == 200:
            return webpack_path
        else:
            return static_path

    else:

        # load the correct file from the manifest.json
        with open(os.path.join(settings.BASE_DIR, 'client/dist', app, 'manifest.json')) as manifest_file:
            manifest = json.load(manifest_file)
            filename = manifest[f'{bundle}.js']
        return static(os.path.join(app, filename))




@register.simple_tag
def manifest(app):
    """Add the webpack chunk manifest to the global scope."""

    if settings.DEBUG:
        return ''

    else:
        with open(os.path.join(settings.BASE_DIR, 'client/dist', app, 'chunk-manifest.json')) as manifest_file:
            manifest = json.load(manifest_file)

        return mark_safe(f"""
        //<![CDATA[
            window.webpackManifest = {json.dumps(manifest)};
        //]]>
        """)
