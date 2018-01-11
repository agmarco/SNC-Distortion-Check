from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission


def login_and_permission_required(permission):
    class LoginAndPermissionRequired(BasePermission):
        def has_permission(self, request, view):
            return request.user.is_authenticated and request.user.has_perm(permission)
    return LoginAndPermissionRequired


def validate_institution(model_class=None, pk_url_kwarg='pk'):
    class ValidateInstitution(BasePermission):
        def has_permission(self, request, view):
            if model_class:
                if pk_url_kwarg not in request.data:
                    return False
                else:
                    obj = get_object_or_404(model_class, pk=request.data[pk_url_kwarg])
            elif callable(getattr(view, 'get_object', None)):
                obj = view.get_object()
            else:
                raise Exception("You must either specify the model_class, or implement the get_object method.")

            if not hasattr(obj, 'institution'):
                raise Exception(f"The property 'institution' was not found on the object {obj}.")

            return request.user.get_institution(request) == obj.institution
    return ValidateInstitution


class CheckLicense(BasePermission):
    def has_permission(self, request, view):
        pass
