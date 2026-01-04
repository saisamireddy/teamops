import threading
from contextlib import contextmanager

_thread_locals = threading.local()


def is_audit_enabled():
    """
    Returns True if audit logging is enabled for the current thread.
    Default is enabled.
    """
    return getattr(_thread_locals, "audit_enabled", True)


@contextmanager
def disable_audit():
    """
    Temporarily disable audit logging within this context.
    Used to prevent audit recursion.
    """
    previous = getattr(_thread_locals, "audit_enabled", True)
    _thread_locals.audit_enabled = False
    try:
        yield
    finally:
        _thread_locals.audit_enabled = previous
