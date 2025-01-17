#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":

    # HACK: set current directory (first position in the path) up a level; this
    # avoids name collisions with importing `celery`; this ensures that
    # manage.py is run with the root at the root of the repository
    sys.path[0] = os.path.dirname(sys.path[0])  

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)
