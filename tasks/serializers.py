from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ("created_by", "is_deleted")

    def validate(self, data):
        project = data.get("project") or self.instance.project
        assignee = data.get("assigned_to")

        if assignee and assignee not in project.members.all():
            raise serializers.ValidationError(
                "Assigned user must be a project member"
            )

        return data
