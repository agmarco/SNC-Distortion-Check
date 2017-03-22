from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied


def check_institution(single_object_class):
    """Checks that the user belongs to the same institution as the object belonging to the CBV."""

    class Inner(single_object_class):
        def dispatch(self, request, *args, **kwargs):
            obj = self.get_object()
            if obj.institution != request.user.institution:
                raise PermissionDenied
            return super(Inner, self).dispatch(request, *args, **kwargs)
    return Inner


def login_and_permission_required(permission, **kwargs):
    """Checks that user is logged in and has the specified permission."""

    def decorator(view):
        return login_required(permission_required(permission, raise_exception=True, **kwargs)(view))
    return decorator
