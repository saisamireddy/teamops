from django.urls import path
from tasks.consumers import EchoConsumer

websocket_urlpatterns=[
    path("ws/echo/",EchoConsumer.as_asgi()),
]
