from django.db.models.signals import post_save
from django.dispatch import receiver

from tasks.models import Task
from tasks.realtime import broadcast_task_event


@receiver(post_save, sender=Task)
def task_realtime_handler(sender, instance, created, **kwargs):
    if instance.is_deleted:
        action = "DELETED"
    elif created:
        action = "CREATED"
    else:
        action = "UPDATED"

    payload = {
        "type": "task.event",
        "action": action,
        "task": {
            "id": instance.id,
            "title": instance.title,
            "status": instance.status,
            "assigned_to": instance.assigned_to.username if instance.assigned_to else None,
        },
    }

    broadcast_task_event(instance.project_id, payload)
