from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView
from rest_framework.exceptions import PermissionDenied
from .models import Task
from .serializers import TaskSerializer
from .permissions import IsProjectMember, CanModifyTask
from projects.models import Project

class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated,IsProjectMember, CanModifyTask]

    def get_queryset(self):
        return (
            Task.objects
            .active()
            .filter(project__members=self.request.user)
            .select_related("project", "assigned_to")
        )

    def perform_create(self, serializer):
        user = self.request.user
        project = serializer.validated_data["project"]

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if user.role not in ["ADMIN", "PM"]:
            raise PermissionDenied("You cannot create tasks")

        serializer.save(created_by=user)

    def perform_destroy(self, instance):
        instance.soft_delete()


class ProjectTaskListCreateView(ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        return (
            Task.objects
            .active()
            .filter(project_id=project_id)
            .select_related("project", "assigned_to")
        )

    def perform_create(self, serializer):
        user = self.request.user
        project_id = self.kwargs["project_id"]
        project = Project.objects.get(id=project_id)

        if user.role not in ["ADMIN", "PM"]:
            raise PermissionDenied("You cannot create tasks")

        serializer.save(
            project=project,
            created_by=user
        )


