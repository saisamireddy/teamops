from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView
from rest_framework.exceptions import PermissionDenied
from .models import Task
from .serializers import TaskSerializer
from .permissions import IsProjectMember, CanModifyTask
from projects.models import Project
from rest_framework.decorators import action
from rest_framework.response import Response

class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated,IsProjectMember, CanModifyTask]

    def get_queryset(self):
        return (
            Task.objects
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

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        task = self.get_object()
        task.is_deleted = False
        task.save()
        return Response({"status": "restored"})


class ProjectTaskListCreateView(ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        qs = Task.objects.filter(project_id=project_id,project__members=self.request.user)

        include_deleted = self.request.query_params.get("deleted")

        if include_deleted == "true":
            return qs.filter(is_deleted=True)

        return qs.filter(is_deleted=False)

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


