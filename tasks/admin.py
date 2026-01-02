from django.contrib import admin
from .models import Task

@admin.action(description="Restore selected tasks (Undo Delete)")
def restore_tasks(modeladmin, request, queryset):
    # This efficiently updates all selected rows in one SQL query
    queryset.update(is_deleted=False)

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
        "created_by"
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

    actions = [restore_tasks]

    def save_model(self, request, obj, form, change):
        # Auto-assign the creator only when creating a NEW task
        if not change:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        # Override the "Delete" button to use Soft Delete
        obj.soft_delete()

    def delete_queryset(self, request, queryset):
        # Override the "Bulk Delete" dropdown to use Soft Delete
        queryset.update(is_deleted=True)

    def get_queryset(self, request):
        #  Pre-fetch related data to avoid N+1 queries
        return super().get_queryset(request).select_related(
            "project", "assigned_to", "created_by"
        )