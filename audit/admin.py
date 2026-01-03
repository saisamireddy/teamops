from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at", "actor", "action",
        "content_type", "object_id", "ip_address",
    )
    list_filter = ("action", "content_type")
    search_fields = ("object_id",)
    list_select_related = ("content_type", "actor")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False