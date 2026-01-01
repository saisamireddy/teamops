from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # What you see in the list view
    list_display = (
        "title", "project", "assigned_to", "status", "priority", "due_date", "is_deleted", "created_at",
    )

    # Filters on the right sidebar
    list_filter = (
        "status", "priority",
        "is_deleted", "project",
    )

    # Search box
    search_fields = (
        "title", "description",
    )
    # Default ordering
    ordering = ("-created_at",)

    # Date drill-down navigation
    date_hierarchy = "created_at"

    # Read-only safety fields
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    # Group fields nicely in the edit form
    fieldsets = (
        ("Task Info", {
            "fields": ("title", "description", "project")
        }),
        ("Assignment & Status", {
            "fields": ("assigned_to", "status", "priority", "due_date")
        }),
        ("Audit", {
            "fields": ("created_by", "is_deleted", "created_at", "updated_at")
        }),
    )
