import inspect

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


def validate_institution(model_class=None, pk_url_kwarg='pk'):
    """
    Checks that the user belongs to the same institution as the object.
    If the decoratee is a class, the object is obtained from view.get_object().
    If decoratee is a function, the object is obtained using the specified model_class and pk_url_kwarg.
    """

    def decorator(view):
        if inspect.isclass(view):
            class Inner(view):
                def dispatch(self, request, *args, **kwargs):
                    obj = self.get_object()  # assume self.get_object() is implemented
                    if obj.institution != request.user.institution:
                        raise PermissionDenied
                    return super(Inner, self).dispatch(request, *args, **kwargs)
            return Inner

        else:
            def inner(request, *args, **kwargs):
                obj = get_object_or_404(model_class, pk=kwargs[pk_url_kwarg])
                if obj.institution != request.user.institution:
                    raise PermissionDenied
                view(request, *args, **kwargs)
            return inner
    return decorator


def login_and_permission_required(permission, **kwargs):
    """Checks that user is logged in and has the specified permission."""

    def decorator(view):
        return login_required(permission_required(permission, raise_exception=True, **kwargs)(view))
    return decorator
