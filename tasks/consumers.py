from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from projects.models import Project

class EchoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        if not user or user.is_anonymous:
            await self.close(code=4001)
            return

        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        await self.send(text_data=json.dumps({
            "user": self.scope["user"].username,
            "echo": text_data
        }))

    async def disconnect(self, close_code):
        pass


class ProjectTaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        project_id = self.scope["url_route"]["kwargs"]["project_id"]

        if not user or user.is_anonymous:
            await self.close(code=4001)
            return

        is_member = await self.is_project_member(user, project_id)
        if not is_member:
            await self.close(code=4003)  # Forbidden
            return

        self.project_group = f"project_{project_id}"

        await self.channel_layer.group_add(
            self.project_group,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "project_group"):
            await self.channel_layer.group_discard(
                self.project_group,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        # For now, just echo back
        await self.send(text_data=json.dumps({
            "message": "connected to project",
            "project": self.project_group
        }))

    async def task_event(self, event):
        event.pop("type", None)
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def is_project_member(self, user, project_id):
        return Project.objects.filter(
            id=project_id,
            members=user
        ).exists()
