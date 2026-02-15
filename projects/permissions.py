from rest_framework.permissions import BasePermission


class CanCreateProject(BasePermission):
    """
    Only Admin or Project Manager can create projects.
    """

    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.role in ["ADMIN", "PM"]
        return True
