from django.db.models.signals import pre_save,post_save
from django.dispatch import receiver
from django.db import transaction
from tasks.models import Task
from tasks.realtime import broadcast_task_event



@receiver(pre_save, sender=Task)
def task_pre_save_handler(sender, instance, **kwargs):
    """
    Store previous is_deleted value on the instance
    so post_save can detect transitions correctly.
    """
    if not instance.pk:
        instance._old_is_deleted = None
        return

    try:
        old = Task.objects.get(pk=instance.pk)
        instance._old_is_deleted = old.is_deleted
    except Task.DoesNotExist:
        instance._old_is_deleted = None


@receiver(post_save, sender=Task)
def task_realtime_handler(sender, instance, created, **kwargs):
    # Determine previous state safely
    old_is_deleted = getattr(instance, "_old_is_deleted", None)

    # Decide action
    if created:
        action = "CREATED"
    elif old_is_deleted is False and instance.is_deleted is True:
        action = "DELETED"
    elif old_is_deleted is True and instance.is_deleted is False:
        action = "RESTORED"
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
