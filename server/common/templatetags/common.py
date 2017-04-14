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
def webpack(bundle):
    """Use the webpack dev server in development, and staticfiles in production."""

    if settings.DEBUG:
        webpack_path = os.path.join('http://0.0.0.0:8080/', bundle)
        static_path = static(bundle)

        try:
            res = requests.get(webpack_path)
        except ConnectionError:
            return static_path

        if res.status_code == 200:
            return webpack_path
        else:
            return static_path

    else:
        try:

            # load the correct file from the manifest.json
            with open(os.path.join(settings.BASE_DIR, 'client/dist/manifest.json')) as manifest_file:
                manifest = json.load(manifest_file)
                filename = manifest[bundle]
            return static(filename)
        except FileNotFoundError:
            return ''


@register.simple_tag
def manifest():
    """Add manifest.js in production."""

    if settings.DEBUG:
        return ''

    else:
        return mark_safe(f'<script src="{webpack("manifest.js")}"></script>')


@register.simple_tag
def chunk_manifest():
    """Add the webpack chunk manifest to the global scope."""

    if settings.DEBUG:
        return ''

    else:
        try:
            with open(os.path.join(settings.BASE_DIR, 'client/dist/chunk-manifest.json')) as chunk_manifest_file:
                chunk_manifest = json.load(chunk_manifest_file)

            return mark_safe(f"""
            <script>
                //<![CDATA[
                    window.webpackManifest = {json.dumps(chunk_manifest)};
                //]]>
            </script>
            """)
        except FileNotFoundError:
            return ''
