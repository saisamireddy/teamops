from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    assigned_username = serializers.CharField(
        source="assigned_to.username",
        read_only=True
    )
    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ("created_by", "is_deleted", "project")

    def validate(self, data):
        project = data.get("project") or getattr(self.instance, "project", None)
        assignee = data.get("assigned_to")

        if not project:
            return data

        if assignee and assignee not in project.members.all():
            raise serializers.ValidationError(
                "Assigned user must be a project member"
            )

        return data
