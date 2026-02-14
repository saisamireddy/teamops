from django.db.models.signals import pre_save, post_save
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from .models import AuditLog
from .utils import (
    is_audit_enabled, disable_audit,
    get_current_user, get_request_meta,
    compute_diff
)

# --- CONFIGURATION ---
from tasks.models import Task

User = get_user_model()

# 1. Add User here to track Registration (Create) and Profile Edits (Update)
AUDITED_MODELS = [Task, User]


def register_audit_signals():
    """Connects signals to all models in AUDITED_MODELS"""
    for model in AUDITED_MODELS:
        pre_save.connect(capture_old_state, sender=model)
        post_save.connect(audit_model_change, sender=model)


# --- AUTHENTICATION HANDLERS ---

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    if not is_audit_enabled(): return
    ip = request.META.get("REMOTE_ADDR")
    ua = request.META.get("HTTP_USER_AGENT")

    with disable_audit():
        AuditLog.objects.create(
            actor=user,
            action="LOGIN",
            content_type=ContentType.objects.get_for_model(user),
            object_id=str(user.pk),
            changes={"status": "Success"},
            ip_address=ip,
            user_agent=ua,
        )


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    if not is_audit_enabled(): return
    ip = request.META.get("REMOTE_ADDR")
    ua = request.META.get("HTTP_USER_AGENT")
    username = credentials.get("username", "unknown")

    with disable_audit():
        AuditLog.objects.create(
            actor=None,
            action="LOGIN_FAILED",
            content_type=None,
            object_id=None,
            changes={"attempted_username": username},
            ip_address=ip,
            user_agent=ua,
        )


# --- DB HANDLERS ---

def capture_old_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._audit_old = None
        return
    try:
        instance._audit_old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._audit_old = None


def audit_model_change(sender, instance, created, **kwargs):
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

    def on_commit():
        if created:
            write_log("CREATE")
            return

        old = getattr(instance, "_audit_old", None)

        # Soft Delete Logic
        if hasattr(instance, 'is_deleted') and hasattr(old, 'is_deleted'):
            if not old.is_deleted and instance.is_deleted:
                write_log("DELETE")
                return
            if old.is_deleted and not instance.is_deleted:
                write_log("RESTORE")
                return

        # Update
        if old:
            # Ignore password, last_login (handled by login signal), and tech fields
            ignored = {"password", "last_login", "updated_at", "created_at", "_state"}
            diff = compute_diff(old, instance, ignored_fields=ignored)
            if diff:
                write_log("UPDATE", diff)

    transaction.on_commit(on_commit)