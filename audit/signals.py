from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal
from django.db import models
from django.utils.functional import Promise

from audit.models import AuditLog
from audit.middleware import get_current_user, get_request_meta
from tasks.models import Task
from audit.utils import is_audit_enabled, disable_audit

IGNORED_FIELDS = {"updated_at", "created_at", "_state"}

@receiver(pre_save, sender=Task)
def capture_old_state(sender, instance, **kwargs):
    # New object → nothing to compare
    if not instance.pk:
        instance._audit_old = None
        return

    try:
        # Fetch the version currently in the Database
        old = sender.objects.get(pk=instance.pk)
        instance._audit_old = old
    except sender.DoesNotExist:
        instance._audit_old = None

# --- HELPER
def serialize_value(value):
    if value is None:
        return None

    # Handle basic types
    if isinstance(value, (int, float, bool)):
        return value

    # Handle Strings & Lazy Strings (e.g. gettext_lazy)
    if isinstance(value, (str, Promise)):
        return str(value)

    # Handle Dates (Standard JSON format)
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    # Handle UUIDs
    if isinstance(value, UUID):
        return str(value)

    # Handle Decimal (Money)
    # FIX: Use str() instead of float() to preserve exact precision
    if isinstance(value, Decimal):
        return str(value)

    # Handle Foreign Keys / Models
    if isinstance(value, models.Model):
        return {
            "id": value.pk,
            "repr": str(value)
        }

    # Fallback for anything else
    return str(value)

def compute_diff(old, new):
    diff = {}

    for field in new._meta.fields:
        name = field.name
        if name in IGNORED_FIELDS:
            continue

        old_val = getattr(old, name)
        new_val = getattr(new, name)

        if old_val != new_val:
            # FIX: Serialize them before adding to dict
            diff[name] = {
                "old": serialize_value(old_val),
                "new": serialize_value(new_val)
            }

    return diff

@receiver(post_save, sender=Task)
def audit_task_change(sender, instance, created, **kwargs):
    # 🔒 Recursion guard
    if not is_audit_enabled():
        return

    user = get_current_user()
    meta = get_request_meta()

    def write_log(action, changes=None):
        with disable_audit():
            AuditLog.objects.create(
                actor=user if user and user.is_authenticated else None,
                action=action,
                content_type=ContentType.objects.get_for_model(instance),
                object_id=str(instance.pk),
                changes=changes,
                ip_address=meta.get("ip"),
                user_agent=meta.get("ua"),
            )

    #  Only log AFTER commit
    def on_commit():
        if created:
            write_log("CREATE")
            return

        old = getattr(instance, "_audit_old", None)
        # If we couldn't fetch the old version, assume Create or Error
        if not old:
            return

        # Soft delete
        if not old.is_deleted and instance.is_deleted:
            write_log("DELETE")
            return

        # Restore
        if old.is_deleted and not instance.is_deleted:
            write_log("RESTORE")
            return

        #  Standard Update
        diff = compute_diff(old, instance)
        if diff:
            write_log("UPDATE", diff)

    transaction.on_commit(on_commit)


