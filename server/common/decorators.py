import inspect
from functools import wraps

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator


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
                    obj = get_object_or_404(model_class, pk=kwargs[pk_url_kwarg])
                elif callable(getattr(instance, 'get_object', None)):
                    obj = instance.get_object()
                else:
                    raise Exception("You must either specify the model_class, or implement the get_object method.")
                if not hasattr(obj, 'institution'):
                    raise Exception(f"The property 'institution' was not found on the object {obj}.")
                if obj.institution != request.user.institution:
                    raise PermissionDenied
                return old_dispatch(instance, request, *args, **kwargs)

            view.dispatch = new_dispatch
            return view

        else:
            @wraps(view)
            def wrapper(request, *args, **kwargs):
                obj = get_object_or_404(model_class, pk=kwargs[pk_url_kwarg])
                if not hasattr(obj, 'institution'):
                    raise Exception(f"The property 'institution' was not found on the object {obj}.")
                if obj.institution != request.user.institution:
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
