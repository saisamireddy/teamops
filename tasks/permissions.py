from rest_framework.permissions import BasePermission

class IsProjectMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user in obj.project.members.all()

class CanModifyTask(BasePermission):
    def has_object_permission(self, request, view, obj):
        user= request.user

        # Admin & PM: full control
        if user.role in ["ADMIN", "PM"]:
            return True

        # Developer: only assigned task
        if user.role == "DEV":
            return obj.assigned_to == user

        return False