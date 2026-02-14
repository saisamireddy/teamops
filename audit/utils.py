import threading
from contextlib import contextmanager
from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID
from django.db import models
from django.utils.functional import Promise

_thread_locals = threading.local()


def set_audit_context(user, meta):
    _thread_locals.user = user
    _thread_locals.meta = meta


def clear_audit_context():
    if hasattr(_thread_locals, "user"): del _thread_locals.user
    if hasattr(_thread_locals, "meta"): del _thread_locals.meta


def get_current_user():
    return getattr(_thread_locals, "user", None)


def get_request_meta():
    return getattr(_thread_locals, "meta", {})


_audit_disabled = False


def is_audit_enabled():
    return not _audit_disabled


@contextmanager
def disable_audit():
    global _audit_disabled
    prev = _audit_disabled
    _audit_disabled = True
    try:
        yield
    finally:
        _audit_disabled = prev


def serialize_value(value):
    if value is None: return None
    if isinstance(value, (int, float, bool)): return value
    if isinstance(value, (str, Promise)): return str(value)
    if isinstance(value, (datetime, date, time)): return value.isoformat()
    if isinstance(value, UUID): return str(value)
    if isinstance(value, Decimal): return str(value)
    if isinstance(value, models.Model): return {"id": value.pk, "repr": str(value)}
    return str(value)


def compute_diff(old, new, ignored_fields=None):
    if ignored_fields is None:
        ignored_fields = {"updated_at", "created_at", "_state"}

    diff = {}
    for field in new._meta.fields:
        name = field.name
        if name in ignored_fields:
            continue

        old_val = getattr(old, name, None)
        new_val = getattr(new, name, None)

        if old_val != new_val:
            diff[name] = {
                "old": serialize_value(old_val),
                "new": serialize_value(new_val)
            }
    return diff