import inspect
from functools import wraps
import logging

from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.utils.safestring import mark_safe

from server.common.models import Machine, Sequence


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
            return method_decorator((login_required, permission_required(permission, raise_exception=True, **kwargs)), name='dispatch')(view)
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


# TODO messages created in the wrapped view are overwritten by the ones created in this decorator
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
            if msg and msg not in [m.message for m in get_messages(request)]:
                messages.info(request, mark_safe(msg))
        except:
            logger.exception('Exception occurred during check machine sequences decorator')

        return response

    return wrapper
