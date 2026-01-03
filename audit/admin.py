from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import AuditLog
from django.utils.html import  format_html_join
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at", "actor", "action",
        "short_changes", "object_id", "ip_address",
    )
    list_filter = ("action", "content_type", "created_at" )
    search_fields = ("object_id","actor__username")
    list_select_related = ("content_type", "actor")
    ordering = ("-created_at",)
    readonly_fields = [f.name for f in AuditLog._meta.fields] + ["pretty_changes"]
    fieldsets = (
        ("Who / When", {
            "fields": ("actor", "ip_address", "user_agent", "created_at")
        }),
        ("What", {
            "fields": ("action", "content_type", "object_id", "object_link")
        }),
        ("Changes", {
            "fields": ("pretty_changes",)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    # --- CUSTOM METHODS ---

    @admin.display(description="Object")
    def object_link(self, obj):
        if not obj.content_type:
            return "-"

        try:
            # 2. Use 'reverse' to dynamically find the correct Admin URL
            # Pattern: admin:app_model_change
            url_name = f"admin:{obj.content_type.app_label}_{obj.content_type.model}_change"
            url = reverse(url_name, args=[obj.object_id])
            items = [(url, obj.content_type.model, obj.object_id)]

            return  format_html_join('', '<a href="{}">{} #{}</a>', items)
        except Exception:
            return f"{obj.content_type.model} #{obj.object_id}"

    @admin.display(description="Changed Fields")
    def short_changes(self, obj):
        if not obj.changes:
            return "-"
        return ", ".join(obj.changes.keys())

    @admin.display(description="Field Changes")
    def pretty_changes(self, obj):
        if not obj.changes:
            return "—"

        lines = []
        for field, change in obj.changes.items():
            old = change.get("old")
            new = change.get("new")
            # 3. Use CSS logic to make it look clean
            lines.append(f"<b>{field}</b>: {old} → {new}")

        # 4. Use <br> for actual line breaks in HTML
        return mark_safe("<br>".join(lines))

    # Optimization
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "actor",
            "content_type",
        )