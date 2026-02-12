from rest_framework import serializers
from .models import Project
from accounts.models import User


class ProjectSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "members",
            "is_archived",
        ]
        read_only_fields = ["owner"]

    def update(self, instance, validated_data):
        members = validated_data.pop("members", None)

        instance = super().update(instance, validated_data)

        if members is not None:
            instance.members.set(members)

        return instance
