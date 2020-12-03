import inspect
import os
from functools import wraps
import logging

from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.utils.safestring import mark_safe

from server.common.models import Machine, Sequence, Institution

from .heroku_api import HerokuAPI

logger = logging.getLogger(__name__)


def validate_institution(model_class=None, pk_url_kwarg='pk'):
    """
    Checks that the user belongs to the same institution as the object.
    If the decoratee is a class, the object is obtained using the specified model_class and pk_url_kwarg if they are
    provided, or view.get_object() otherwise.
    If decoratee is a function, the object is obtained using the specified model_class and pk_url_kwarg.
    """

    def decorator(view):
        if inspect.isclass(view):
            old_dispatch = view.dispatch

            def new_dispatch(instance, request, *args, **kwargs):
                if model_class:
                    if pk_url_kwarg not in kwargs:
                        raise PermissionDenied
                    obj = get_object_or_404(model_class, pk=kwargs[pk_url_kwarg])
                elif callable(getattr(instance, 'get_object', None)):
                    obj = instance.get_object()
                else:
                    raise Exception("You must either specify the model_class, or implement the get_object method.")
                if not hasattr(obj, 'institution'):
                    raise Exception(f"The property 'institution' was not found on the object {obj}.")
                if obj.institution is None:
                    messages.warning(request, '''Please log out of admin to process scans.''')
                    return HttpResponseRedirect('/')
                if obj.institution != request.user.get_institution(request):
                    raise PermissionDenied
                return old_dispatch(instance, request, *args, **kwargs)

            view.dispatch = new_dispatch
            return view

        else:
            @wraps(view)
            def wrapper(request, *args, **kwargs):
                if pk_url_kwarg not in kwargs:
                    raise PermissionDenied
                obj = get_object_or_404(model_class, pk=kwargs[pk_url_kwarg])
                if not hasattr(obj, 'institution'):
                    raise Exception(f"The property 'institution' was not found on the object {obj}.")

                if obj.institution != request.user.get_institution(request):
                    raise PermissionDenied

                return view(request, *args, **kwargs)

            return wrapper

    return decorator


def login_and_permission_required(permission, **kwargs):
    """Checks that user is logged in and has the specified permission."""

    def decorator(view):
        if inspect.isclass(view):
            return method_decorator((login_required, permission_required(permission, raise_exception=True, **kwargs)),
                                    name='dispatch')(view)
        else:
            return login_required(permission_required(permission, raise_exception=True, **kwargs)(view))

    return decorator


def institution_required(view):
    """If the user is an admin, check that there is an active institution, and if not, prompt the admin to set one."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser and request.user.get_institution(request) is None:
            return render(request, 'common/admin_error.html')
        else:
            return view(request, *args, **kwargs)

    return wrapper


def intro_tutorial(view):
    """If there are no machines or sequences, display a message alerting the user to add them."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        response = view(request, *args, **kwargs)

        try:
            institution = request.user.get_institution(request)
            machines = Machine.objects.filter(institution=institution).active()
            sequences = Sequence.objects.filter(institution=institution).active()

            no_machines = machines.count() == 0
            no_sequences = sequences.count() == 0

            msg = None

            if request.user.has_perm('common.configuration'):
                config_url = reverse('configuration')
                configuration_link = f'<a href="{config_url}">{{}}</a>'

                if no_machines and no_sequences:
                    msg = f"Welcome to CIRS's Distortion Check software.  Before you can begin uploading " \
                          f"MRIs to analyze, please {configuration_link.format('add one machine and one sequence')}."
                elif no_machines:
                    msg = f"You must {configuration_link.format('configure at least one machine')} " \
                          f"before you can begin uploading MRIs to analyze."
                elif no_sequences:
                    msg = f"You must {configuration_link.format('configure at least one sequence')} " \
                          f"before you can begin uploading MRIs to analyze."
            else:
                if no_machines or no_sequences:
                    msg = "A user with configuration privileges must setup at least one machine and one sequence " + \
                          "must be configured before you can begin uploading MRIs to analyze."

            storage = get_messages(request)
            if msg and msg not in [m.message for m in storage]:
                messages.info(request, mark_safe(msg))
            storage.used = False
        except:
            logger.exception('Exception occurred during check machine sequences decorator')

        return response

    return wrapper


expiration_warning_cutoff_days = 30
expiration_warning_cutoff_scans = 20


def check_license(check_scans=False):
    """If the license is expired or there are 0 scans remaining, make the view unavailable."""

    def decorator(view):

        @wraps(view)
        def wrapper(request, *args, **kwargs):
            institution = request.user.get_institution(request)
            license_expiration_date = institution.license_expiration_date
            scans_remaining = institution.scans_remaining
            now = datetime.now().date()

            if license_expiration_date is not None and license_expiration_date <= now:
                return render(request, 'common/license_expired.html', status=403)
            elif check_scans and scans_remaining == 0:
                return render(request, 'common/license_expired.html', status=403)

            expiration_warning_cutoff_date = now + timedelta(days=expiration_warning_cutoff_days)
            time_warning = (
                    license_expiration_date is not None
                    and license_expiration_date <= expiration_warning_cutoff_date
            )
            count_warning = (
                    scans_remaining is not None
                    and scans_remaining <= expiration_warning_cutoff_scans
            )
            days_remaining = None if license_expiration_date is None else (license_expiration_date - now).days
            msg = None
            if time_warning and count_warning:
                msg = f"You have {_pluralize(scans_remaining, 'scan')} remaining and your " + \
                      f"license expires in {_pluralize(days_remaining, 'day')}. " + \
                      "Contact CIRS support to update your license."
            elif count_warning:
                msg = f"You have {_pluralize(scans_remaining, 'scan')} remaining. " + \
                      "Contact CIRS support to acquire more scans."
            elif time_warning:
                msg = f"Your license expires in {_pluralize(days_remaining, 'day')}. " + \
                      "Contact CIRS support to renew your license."

            if msg is not None:
                _add_warning_if_not_present_already(request, msg)

            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def manage_worker_server(view):
    if not os.getenv('HEROKU_APP_NAME'):
        return view
    else:
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            try:
                heroku_connection = HerokuAPI()
                if not heroku_connection.worker_is_on():
                    heroku_connection.start_worker()
                return view(request, *args, **kwargs)
            except Exception:
                messages.warning(request, '''A server error occurred. We can not process or refresh any scans at the moment. 
                Our technical staff have been notified and will be looking into this with the utmost urgency.''')
                return HttpResponseRedirect('/')

        return wrapper


def _pluralize(count, word):
    return f'{count} {word}s' if count != 1 else f'{count} {word}'


def _add_warning_if_not_present_already(request, new_message):
    storage = messages.get_messages(request)
    message_exists = False
    for existing_message in storage:
        if existing_message.message == new_message:
            message_exists = True
            break
    if not message_exists:
        messages.warning(request, new_message)
    storage.used = False
