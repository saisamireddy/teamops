from django.urls import path
from tasks.consumers import EchoConsumer, ProjectTaskConsumer

websocket_urlpatterns=[
    path("ws/echo/",EchoConsumer.as_asgi()),
    path("ws/projects/<int:project_id>/", ProjectTaskConsumer.as_asgi()),
]
