from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import User
from .models import Project
from .serializers import ProjectSerializer
from .permissions import CanCreateProject


class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, CanCreateProject]

    def get_queryset(self):
        user = self.request.user

        return (
            Project.objects
            .filter(
                Q(owner=user) | Q(members=user),
                is_archived=False
            )
            .distinct()
        )

    def perform_create(self, serializer):
        project=serializer.save(owner=self.request.user)
        project.members.add(self.request.user)

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        project = self.get_object()

        members = project.members.all().values("id", "username")

        return Response(list(members))
