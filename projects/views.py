from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Project
from .serializers import ProjectSerializer
from .permissions import CanCreateProject


class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, CanCreateProject]

    # -------------------------
    # Queryset control
    # -------------------------
    def get_queryset(self):
        user = self.request.user

        qs = (
            Project.objects
            .filter(Q(owner=user) | Q(members=user))
            .distinct()
            .prefetch_related("members")
        )

        archived = self.request.query_params.get("archived")

        if archived == "true":
            return qs.filter(is_archived=True)

        return qs.filter(is_archived=False)

    # -------------------------
    # Create project
    # -------------------------
    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)
        project.members.add(self.request.user)

    # -------------------------
    # Update permission guard
    # -------------------------
    def perform_update(self, serializer):
        project = self.get_object()

        if self.request.user not in [project.owner] and \
           self.request.user.role not in ["ADMIN", "PM"]:
            raise PermissionDenied("Cannot modify this project")

        serializer.save()

    # -------------------------
    # Archive project
    # -------------------------
    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        project = self.get_object()

        if request.user not in [project.owner] and \
           request.user.role not in ["ADMIN", "PM"]:
            raise PermissionDenied("Not allowed")

        project.is_archived = True
        project.save()

        return Response({"status": "archived"})

    # -------------------------
    # Unarchive project
    # -------------------------
    @action(detail=True, methods=["post"])
    def unarchive(self, request, pk=None):
        project = get_object_or_404(Project, pk=pk)

        if request.user not in [project.owner] and \
           request.user.role not in ["ADMIN", "PM"]:
            raise PermissionDenied("Not allowed")

        project.is_archived = False
        project.save()

        return Response({"status": "unarchived"})

    # -------------------------
    # Soft delete project
    # -------------------------
    def perform_destroy(self, instance):
        if self.request.user != instance.owner and \
           self.request.user.role != "ADMIN":
            raise PermissionDenied("Only owner/admin can delete")

        instance.is_archived = True
        instance.save()

    # -------------------------
    # Members list
    # -------------------------
    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        project = self.get_object()

        members = project.members.all().values(
            "id",
            "username"
        )

        return Response(list(members))
