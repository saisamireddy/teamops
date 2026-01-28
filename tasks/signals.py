from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from tasks.models import Task
from tasks.realtime import broadcast_task_event


@receiver(post_save, sender=Task)
def task_realtime_handler(sender, instance, created, **kwargs):
    # Determine previous state safely
    old_is_deleted = None

    if instance.pk:
        try:
            old = Task.objects.get(pk=instance.pk)
            old_is_deleted = old.is_deleted
        except Task.DoesNotExist:
            pass

    # Decide action
    if created:
        action = "CREATED"
    elif old_is_deleted and not instance.is_deleted:
        action = "RESTORED"
    elif not old_is_deleted and instance.is_deleted:
        action = "DELETED"
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
            "is_deleted": instance.is_deleted,
        },
    }

    transaction.on_commit(
        lambda: broadcast_task_event(instance.project_id, payload)
    )
