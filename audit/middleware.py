import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.functional import SimpleLazyObject
from rest_framework_simplejwt.authentication import JWTAuthentication
from .utils import set_audit_context, clear_audit_context


def get_jwt_user(request):
    """
    Manual JWT authentication for middleware.
    """
    try:
        # Check standard Authorization header
        header = request.META.get('HTTP_AUTHORIZATION')
        if not header:
            return None

        # Standard DRF JWT Auth flow
        jwt_auth = JWTAuthentication()
        try:
            # authenticate() returns (user, token) or None
            result = jwt_auth.authenticate(request)
            if result:
                return result[0]  # Return the user object
        except Exception:
            return None

    except Exception:
        return None
    return None


class AuditUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Try standard Django Session Auth first
        user = getattr(request, "user", None)

        # 2. If User is Anon, try to authenticate via JWT
        if not user or not user.is_authenticated:
            jwt_user = get_jwt_user(request)
            if jwt_user:
                request.user = jwt_user  # Attach to request for views to use
                user = jwt_user

        # 3. Set the context for the signals
        set_audit_context(
            user=user,
            meta={
                "ip": request.META.get("REMOTE_ADDR"),
                "ua": request.META.get("HTTP_USER_AGENT"),
            }
        )

        try:
            response = self.get_response(request)
        finally:
            clear_audit_context()

        return response