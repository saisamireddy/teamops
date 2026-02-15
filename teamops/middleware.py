from urllib.parse import parse_qs

from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections

from channels.db import database_sync_to_async

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class JWTAuthMiddleware:
    """
    Authenticate WebSocket connections using JWT (?token=...)
    """

    def __init__(self, inner):
        self.inner = inner
        self.jwt_auth = JWTAuthentication()

    async def __call__(self, scope, receive, send):
        close_old_connections()

        scope["user"] = AnonymousUser()

        query_params = parse_qs(scope.get("query_string", b"").decode())
        token = query_params.get("token")

        if token:
            try:
                user = await self.get_user(token[0])
                scope["user"] = user
            except (InvalidToken, TokenError):
                pass

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        validated_token = self.jwt_auth.get_validated_token(token)
        return self.jwt_auth.get_user(validated_token)
