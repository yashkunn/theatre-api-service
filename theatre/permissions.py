from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_staff:
            return True

        if (
            request.method in SAFE_METHODS
            and request.user
            and request.user.is_authenticated
        ):
            return True

        return False
