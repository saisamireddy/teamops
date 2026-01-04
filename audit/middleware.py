import threading

_thread_locals = threading.local()


def get_current_user():
    return getattr(_thread_locals, "user", None)


def get_request_meta():
    return getattr(_thread_locals, "meta", {})


class AuditUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            _thread_locals.user = getattr(request, "user", None)
            _thread_locals.meta = {
                "ip": request.META.get("REMOTE_ADDR"),
                "ua": request.META.get("HTTP_USER_AGENT"),
            }
            return self.get_response(request)
        finally:
            # 🔒 CRITICAL: prevent thread-local leakage
            if hasattr(_thread_locals, "user"):
                del _thread_locals.user
            if hasattr(_thread_locals, "meta"):
                del _thread_locals.meta
