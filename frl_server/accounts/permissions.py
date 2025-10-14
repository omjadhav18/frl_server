from rest_framework.permissions import BasePermission


class IsCarUser(BasePermission):
    """
    Allows access only to users with role = CAR
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "CAR"


class IsAdminUser(BasePermission):
    """
    Allows access only to ADMIN users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "ADMIN"
    