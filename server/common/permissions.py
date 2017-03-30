from rest_framework.permissions import BasePermission


def login_and_permission_required(permission):
    class LoginAndPermissionRequired(BasePermission):
        def has_permission(self, request, view):
            return request.user.is_authenticated and request.user.has_perm(permission)
    return LoginAndPermissionRequired
