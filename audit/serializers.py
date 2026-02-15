from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    actor_email = serializers.ReadOnlyField(source='actor.email')
    entity_type = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'action',
            'actor_name',
            'actor_email',
            'entity_type',
            'object_id',
            'changes',
            'ip_address',
            'created_at'
        ]

    def get_actor_name(self, obj):
        if obj.actor:
            return obj.actor.username
        if obj.action == "LOGIN_FAILED":
            return f"Unknown ({obj.changes.get('attempted_username', '?')})"
        return "System"

    def get_entity_type(self, obj):
        if obj.content_type:
            return obj.content_type.model
        return "Security"