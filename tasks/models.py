from django.db import models
from projects.models import Project
from accounts.models import User

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
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
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

    def __str__(self):
        return self.title
