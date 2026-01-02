from django.db import models
# from projects.models import Project
from accounts.models import User
from django.core.exceptions import ValidationError

class TaskQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

class Task(models.Model):
    PRIORITY = (
        ("LOW", "Low"),
        ("MED", "Medium"),
        ("HIGH", "High"),
        ("CRIT", "Critical"),
    )

    STATUS = (
        ("TODO", "Todo"),
        ("IN_PROGRESS", "In Progress"),
        ("BLOCKED", "Blocked"),
        ("DONE", "Done"),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="tasks")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,related_name="assigned_tasks")
    priority = models.CharField(max_length=5, choices=PRIORITY, default="MED")
    status = models.CharField(max_length=15, choices=STATUS, default="TODO")
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_tasks")
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TaskQuerySet.as_manager()

    def soft_delete(self):
        self.is_deleted = True
        self.save(update_fields=["is_deleted"])
    def clean(self):

        if self.pk:
            # Fetch the version currently in the database
            db_task = Task.objects.only("is_deleted").get(pk=self.pk)
            if db_task.is_deleted and self.is_deleted:
                raise ValidationError("Cannot modify a task that has been deleted.")

        if self.assigned_to and self.project:

            if not self.project.members.filter(id=self.assigned_to.id).exists():
                raise ValidationError({
                    "assigned_to": f"User '{self.assigned_to.username}' is not a member of project '{self.project.name}'."
                })

    def save(self, *args, **kwargs):

        if kwargs.get("update_fields"):
            if "is_deleted" in kwargs["update_fields"]:
                super().save(*args, **kwargs)
                return

        self.full_clean()  # Enforce validation on every normal save
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
