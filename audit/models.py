from django.db import models
from accounts.models import User

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("RESTORE", "Restore"),
    )

    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs"
    )

    action = models.CharField(max_length=10, choices=ACTION_CHOICES)

    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50)

    changes = models.JSONField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} {self.model_name}({self.object_id})"


